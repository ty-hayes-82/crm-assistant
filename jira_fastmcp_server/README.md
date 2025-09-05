# Jira FASTMCP Server

This directory contains a simple FASTMCP server for reading and querying Jira tickets from a CSV file.

## How to run

1.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the server:
    ```bash
    python -m jira_fastmcp_server.main
    ```

3.  In a separate terminal, you can interact with the agent. For example, using `adk run`:
    ```bash
    adk run -a jira_agent/root_agent.yaml "load the jira csv"
    ```
    Then:
    ```bash
    adk run -a jira_agent/root_agent.yaml "list the first 5 tickets"
    ```

## Files

-   `server.py`: Runs the FASTMCP server.
-   `tools.py`: Defines the tools for interacting with the Jira CSV data.
-   `main.py`: The main entry point for the server.
