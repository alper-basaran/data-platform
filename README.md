# platform

To Run the Project Locally: make create
To Stop the Project and destroy all the resources created: make teardown

# once it all done, go back to platform folder to revisit:
- Making postgres results persistent, otherwise hard to demonstrate results? 
- Try making the cluster single node, see if it resolves port foprwarding issue
- Try helm charts for minio and postgres, this way we can push environment variables during CD
