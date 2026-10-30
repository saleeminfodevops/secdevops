// Jenkinsfile/container-security.groovy
pipeline {
    agent any
    environment {
        SEVERITY_THRESHOLD = 'HIGH,CRITICAL'
        IMAGE_TO_SCAN      = 'ubuntu:18.04'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Container Scan') {
            steps {
                script {
                    sh """
                    docker run --rm aquasec/trivy:latest image \
                      --exit-code 1 \
                      --severity ${env.SEVERITY_THRESHOLD} \
                      ${env.IMAGE_TO_SCAN}
                    """
                }
            }
        }
    }
}
