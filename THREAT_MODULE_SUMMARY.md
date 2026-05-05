# Threat Management Module – Implementation Summary

**Author:** Waleed Ahmad

This module provides the core functionality for threat modeling:
- list_models() – displays all models belonging to the current user
- create_model() – creates a new threat model
- model_detail() – shows a model and its threats
- dd_threat() – adds a new threat with STRIDE/DREAD
- delete_model() – removes a threat model (ownership checked)

Security: Every route verifies that the model belongs to the authenticated user before allowing access.
