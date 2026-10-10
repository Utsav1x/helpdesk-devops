// Explicit first-run bootstrap for this private, single-user academic Jenkins.
import jenkins.model.Jenkins
import jenkins.model.JenkinsLocationConfiguration
import jenkins.install.InstallState
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.model.User
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.SecretBytes
import com.cloudbees.plugins.credentials.domains.Domain
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl
import org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject
import org.jenkinsci.plugins.workflow.multibranch.WorkflowBranchProjectFactory
import org.jenkinsci.plugins.github_branch_source.GitHubSCMSource
import org.jenkinsci.plugins.github_branch_source.BranchDiscoveryTrait
import jenkins.branch.BranchSource
import com.cloudbees.hudson.plugins.folder.computed.PeriodicFolderTrigger

if (System.getenv('HELPDESK_BOOTSTRAP') != 'true') { return }
def jenkins = Jenkins.get()
def marker = new File(jenkins.rootDir, 'helpdesk-bootstrap.complete')
if (marker.exists()) { println('Helpdesk bootstrap already completed; preserving configuration.'); return }
def directory = new File('/run/helpdesk-bootstrap')
def read = { name ->
    def file = new File(directory, name)
    if (!file.isFile()) { throw new IllegalStateException('Missing bootstrap file: ' + name) }
    file.getText('UTF-8').trim()
}
def account = read('github-user.txt')
def token = read('github-token.txt')
def repository = read('repository.txt').split('/')
def password = read('jenkins-admin-password.txt')
if (repository.length != 2 || password.length() < 24) { throw new IllegalArgumentException('Invalid bootstrap inputs') }
// Refuse to replace an existing administrator's security configuration.
if (User.getAll().any { it.getProperty(HudsonPrivateSecurityRealm.Details.class) != null }) {
    throw new IllegalStateException('Existing Jenkins users detected. Use the manual setup guide; no security settings changed.')
}
def realm = new HudsonPrivateSecurityRealm(false)
realm.createAccount('helpdesk-admin', password)
jenkins.setSecurityRealm(realm)
def authorization = new FullControlOnceLoggedInAuthorizationStrategy()
authorization.setAllowAnonymousRead(false)
jenkins.setAuthorizationStrategy(authorization)
jenkins.setNumExecutors(1)
JenkinsLocationConfiguration.get().setUrl('http://localhost:8088/')
// Import checkout credentials and both secret-file environments without logging values.
def store = SystemCredentialsProvider.getInstance().getStore()
store.addCredentials(Domain.global(), new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL,
    'github-repo-read', 'GitHub checkout and discovery for the local lab', account, token))
['production', 'staging'].each { environment ->
    def filename = environment + '.env'
    def content = new File(directory, filename).bytes
    store.addCredentials(Domain.global(), new FileCredentialsImpl(CredentialsScope.GLOBAL,
        'todo-' + environment + '-env', environment + ' application configuration', filename, SecretBytes.fromBytes(content)))
}
// Discover trusted repository branches only; do not build fork pull requests.
def job = jenkins.createProject(WorkflowMultiBranchProject.class, 'helpdesk')
def source = new GitHubSCMSource(repository[0], repository[1])
source.setId('helpdesk-github')
source.setCredentialsId('github-repo-read')
source.setTraits([new BranchDiscoveryTrait(3)])
job.getSourcesList().add(new BranchSource(source))
def factory = new WorkflowBranchProjectFactory()
factory.setScriptPath('Jenkinsfile')
job.setProjectFactory(factory)
// Polling works locally without publishing Jenkins through a tunnel.
job.addTrigger(new PeriodicFolderTrigger('1m'))
job.save()
jenkins.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)
jenkins.save()
marker.text = 'Bootstrap completed; credentials are held by Jenkins.\n'
job.scheduleBuild2(0)
println('Helpdesk job created. Initial branch scan scheduled; periodic scans run every minute.')
