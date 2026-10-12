// Trusted local academic repository only: Docker socket access controls the host.
pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds(); skipDefaultCheckout(true) }
  parameters {
    string(name: 'NOTIFY_EMAIL', defaultValue: '', description: 'Optional recipient after SMTP is configured; otherwise notifications appear in the build log.')
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'mkdir -p reports; rm -f reports/unit-tests.xml reports/smoke.txt'
        script {
          env.DEPLOY_ENV = env.BRANCH_NAME == 'main' ? 'production' : 'staging'
          env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
          env.IMAGE_TAG = "${env.GIT_COMMIT.take(12)}-${env.BUILD_NUMBER}"
        }
      }
    }
    stage('Install deps') {
      steps { sh 'python3 -m venv .venv && .venv/bin/pip install -r backend/requirements-dev.txt' }
    }
    stage('Unit tests') {
      steps { sh 'mkdir -p reports && cd backend && ../.venv/bin/python -m pytest tests -q --junitxml=../reports/unit-tests.xml' }
    }
    stage('Build images') {
      // Feature builds use a separate repository; they never receive environment secrets.
      steps {
        sh '''
          docker build -t todo-ci-backend:$IMAGE_TAG backend
          docker build -t todo-ci-frontend:$IMAGE_TAG frontend
        '''
      }
    }
    stage('Deploy') {
      when { anyOf { branch 'main'; branch 'develop' } }
      steps {
        script {
          lock(resource: "todo-${env.DEPLOY_ENV}") {
            withCredentials([file(credentialsId: "todo-${env.DEPLOY_ENV}-env", variable: 'ENV_FILE')]) {
              sh '''
                docker tag todo-ci-backend:$IMAGE_TAG todo-$DEPLOY_ENV-backend:$IMAGE_TAG
                docker tag todo-ci-frontend:$IMAGE_TAG todo-$DEPLOY_ENV-frontend:$IMAGE_TAG
                bash scripts/deploy.sh "$DEPLOY_ENV" "$ENV_FILE" "$IMAGE_TAG"
              '''
            }
          }
        }
      }
    }
    stage('Smoke test') {
      when { anyOf { branch 'main'; branch 'develop' } }
      // deploy.sh gates/rolls back under the same lock; show its report in a distinct stage.
      steps { sh 'test -s reports/smoke.txt && cat reports/smoke.txt' }
    }
    stage('Monitoring') {
      when { branch 'develop' }
      steps {
        lock(resource: 'todo-staging') {
          withCredentials([file(credentialsId: 'todo-staging-env', variable: 'ENV_FILE')]) {
            sh 'bash scripts/monitoring.sh staging "$ENV_FILE"'
          }
        }
      }
    }
  }
  post {
    always {
      junit testResults: 'reports/unit-tests.xml', allowEmptyResults: true
      archiveArtifacts artifacts: 'reports/*', allowEmptyArchive: true
    }
    success {
      echo 'SUCCESS: tests/build completed; eligible branches passed deployment smoke tests.'
      script { if (params.NOTIFY_EMAIL?.trim()) { mail to: params.NOTIFY_EMAIL, subject: "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}", body: "Build: ${env.BUILD_URL}" } }
    }
    failure {
      echo 'FAILURE: inspect logs. A failed deployment attempts automatic rollback; check its result.'
      script { if (params.NOTIFY_EMAIL?.trim()) { mail to: params.NOTIFY_EMAIL, subject: "FAILURE: ${env.JOB_NAME} #${env.BUILD_NUMBER}", body: "Build: ${env.BUILD_URL}" } }
    }
  }
}
