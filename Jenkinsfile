pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "myapp:${BUILD_NUMBER}"
        SEVERITY_THRESHOLD = "HIGH"
    }
    
    stages {
        stage('Build Image') {
            steps {
                script {
                    sh 'docker build -t ${IMAGE_NAME} .'
                }
            }
        }
        
        stage('Scan for Vulnerabilities') {
            steps {
                script {
                    sh '''
                        trivy image \
                          --severity ${SEVERITY_THRESHOLD},CRITICAL \
                          --exit-code 1 \
                          --format json \
                          --output scan-results.json \
                          ${IMAGE_NAME}
                    '''
                }
            }
        }
        
        stage('Parse Results') {
            steps {
                script {
                    sh 'python3 scripts/parse_trivy_results.py'
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*.json', allowEmptyArchive: true
        }
        failure {
            sh 'echo "Build failed due to vulnerabilities"'
        }
    }
}
