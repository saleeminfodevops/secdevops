pipeline {
    agent any

    environment {
        IMAGE_NAME         = 'my-app'
        IMAGE_TAG          = "${BUILD_NUMBER}"
        SEVERITY_LEVEL     = 'HIGH,CRITICAL' // Controlled threshold parameters (Sprint 2)
        SLACK_CREDENTIAL_ID = 'slack-webhook-secret-id' // Setup in Jenkins Credentials
    }

    stages {
        stage('Checkout Source') {
            steps {
                checkout scm
            }
        }

        stage('Build Container Image') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                }
            }
        }

        stage('Automated Vulnerability Scan') {
            steps {
                script {
                    echo "Initiating image scan phase using Trivy..."
                    
                    // Run scanner, export structured JSON report, map exceptions using .trivyignore, and exit with code 1 if threshold breached (Sprint 1, 2, 5)
                    try {
                        sh """
                            trivy image \
                            --format json \
                            --output trivy-report.json \
                            --severity ${SEVERITY_LEVEL} \
                            --exit-code 1 \
                            --ignore-unfixed \
                            .trivyignore \
                            ${IMAGE_NAME}:${IMAGE_TAG}
                        """
                        currentBuild.result = 'SUCCESS'
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        error("Pipeline broke: High/Critical vulnerabilities detected above threshold limits.")
                    }
                }
            }
        }
    }

    post {
        always {
            // Archive report module (Sprint 3)
            archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true, fingerprint: true
        }
        success {
            // Success alerts (Sprint 3)
            slackSend (
                color: '#00FF00',
                message: "SUCCESSFUL: Security Scan Passed for ${IMAGE_NAME}:${IMAGE_TAG}. No blocking vulnerabilities detected."
            )
        }
        failure {
            // Critical vulnerability alerts (Sprint 3)
            slackSend (
                color: '#FF0000',
                message: "CRITICAL ALERT: Security Scan Failed for ${IMAGE_NAME}:${IMAGE_TAG}. Build blocked due to High/Critical vulnerabilities."
            )
        }
    }
}
