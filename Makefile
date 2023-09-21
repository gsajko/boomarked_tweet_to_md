lint: ## Run the code linter.
	ruff ./


style:
	black .
	ruff ./ --fix
	@echo "The style pass! ✨ 🍰 ✨"	