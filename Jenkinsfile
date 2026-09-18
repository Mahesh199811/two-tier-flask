pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'two-tier-flask'
        APP_PORT = '80'
        DB_HOST = 'mysql'
        DB_USER = 'appuser'
        DB_PASSWORD = 'apppassword'
        DB_NAME = 'appdb'
        MYSQL_ROOT_PASSWORD = 'rootpassword'
        MYSQL_DATABASE = 'appdb'
        MYSQL_USER = 'appuser'
        MYSQL_PASSWORD = 'apppassword'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker compose down --remove-orphans'
                sh 'docker compose up -d'
            }
        }

        stage('Verify Containers') {
            steps {
                sh 'docker compose ps'
            }
        }

        stage('Health Check') {
            steps {
                sh 'sleep 10'
                sh "curl -f http://localhost:${APP_PORT}/health"
            }
        }
    }

    post {
        success {
            echo 'Deployment successful!'
        }

        failure {
            echo 'Deployment failed!'
        }
    }
}
