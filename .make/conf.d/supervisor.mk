# Makefile fragment for Supervisor-related tasks

# React Restart Supervisor Server
.PHONY: restart-test-server
restart-test-server:
	@echo "Restarting testserver supervisor service ($(REACT__SUPERVISOR_SERVICE))"
	@sudo supervisorctl restart $(REACT__SUPERVISOR_SERVICE)
	@echo "Testserver restarted"

# Help message
.PHONY: help
help::
	@echo "  $(TEXT_UNDERLINE)Supervisor:$(TEXT_UNDERLINE_END)"
	@echo "    restart-test-server   Restart the testserver supervisor service"
