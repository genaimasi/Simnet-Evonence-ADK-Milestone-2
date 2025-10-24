# Simnet-Evonence-ADK-Milestone-2
This repository contains the source code for the SimnetAgent, a generative AI agent built with Google's Agent Development Kit (ADK).
SimnetAgent (ADK) - Real-time Aerospace Design Advisor
This repository contains the source code for the SimnetAgent, a generative AI agent built with Google's Agent Development Kit (ADK). This agent serves as a real-time, expert aerospace design advisor, representing the Proof of Concept (PoC) for Milestone 2.

The agent is designed to analyze complex drone and aircraft design specifications, provided as either text or image-based inputs (like sketches or diagrams), and provide deep engineering feedback. It automatically logs all interactions to a dedicated BigQuery table for future analysis and model training.

Features
Expert Persona: The agent embodies the persona of SimnetAgent, an expert in aerospace engineering and simulation, guided by the instructions in prompts.py.

Multi-modal Input: The agent is configured to accept both text queries and image uploads, with the before_model_callback in agent.py detecting if an image is part of the user's input.

Automatic BigQuery Logging: Every conversation turn is automatically captured and logged to BigQuery.

Dataset: simnet_aero_bot (auto-created if not present)

Table: simnet_conversations (auto-created if not present)

Rich Callback Integration:

before_model_callback: Securely creates/retrieves a session_id, captures the precise user_query, and detects image inputs.

after_model_callback: Captures the agent_response, calculates the response_time_ms, and calls the ConversationLogger to write the data to BigQuery.

Scalable Deployment: The agent is packaged for serverless deployment on Google Cloud Run.

Integrated Dev UI: The deployment command includes the --with_ui flag, which automatically bundles the ADK's developer web UI for immediate testing and interaction with the deployed agent.

Technology Stack
Framework: Google Agent Development Kit (ADK)

Serving: Google Cloud Run

Logging: Google BigQuery

Core Model: gemini-2.5-pro (as defined in agent.py)

Prerequisites
A Google Cloud Project (e.g., simnet-staging).

The gcloud CLI installed and authenticated (gcloud auth login).

Python 3.10+ and pip installed.

The google-adk and google-cloud-bigquery libraries:

Bash

pip install google-adk google-cloud-bigquery
Required IAM Permissions for the user or service account deploying the agent:

roles/run.admin (to deploy to Cloud Run)

roles/bigquery.dataEditor (to create/write to the BigQuery table)

roles/iam.serviceAccountUser (to assign the runtime identity)

Project Structure
Your project directory should be structured as follows. The deploy command is run from outside the simnet_agent package folder.



├── cloud_run_deploy.sh
└── simnet_agent/
    ├── __init__.py
    ├── adk_config.yaml
    ├── agent.py
    ├── bigquery_logger.py
    └── prompts.py

    
Configuration
The BigQuery logger (bigquery_logger.py) will automatically use environment variables. While GOOGLE_CLOUD_PROJECT is the only one strictly required (as the others have defaults), you can set them all:

Bash

export GOOGLE_CLOUD_PROJECT="simnet-staging"
export BIGQUERY_DATASET_ID="simnet_aero_bot"
export BIGQUERY_TABLE_ID="simnet_conversations"
export GOOGLE_CLOUD_LOCATION="us-central1"
The adk_config.yaml is included to ensure that any uploaded images are correctly handled in memory by the ADK runner.



Deployment
Ensure you have authenticated with gcloud and set your project:

Bash

gcloud config set project simnet-staging
From the root directory (the one containing the simnet_agent folder), run the deployment script:

Bash

./cloud_run_deploy.sh
or just paste the command:

Bash

adk deploy cloud_run \
  --project=simnet-staging \
  --region=us-central1 \
  --service_name=simnet-agent \
  --app_name=Simnet_Agent1 \
  --with_ui \
  simnet_agent
The ADK CLI will package your agent, build a container, push it to Artifact Registry, and deploy it to Cloud Run. This process may take a few minutes.

How to Use
Upon successful deployment, the adk deploy command will output a Service URL (e.g., https://simnet-agent-....a.run.app).

Open this URL in your web browser.

You will see the ADK's built-in developer web UI.

You can now interact with the deployed SimnetAgent:

Text Query: Type Design a quadcopter drone for aerial photography with a 30-minute flight time.

Image Query: Upload a sketch of a drone's wing design and ask, Analyze the aerodynamics of this wing shape.

After each interaction, navigate to the BigQuery console in your Google Cloud project.

Query your table to see the new log entry:

SQL

SELECT *
FROM `simnet_staging.simnet_aero_bot.simnet_conversations`
ORDER BY timestamp DESC
LIMIT 10;
