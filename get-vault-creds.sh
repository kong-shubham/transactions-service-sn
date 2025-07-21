#!/usr/bin/env bash

role_id_response=$(curl -s --header "X-Vault-Token: root" http://localhost:8200/v1/auth/approle/role/transactions-role/role-id)
role_id=$(echo "${role_id_response}" | jq -r '.data.role_id')
echo "role-id: $role_id"

secret_id_response=$(curl -s --header "X-Vault-Token: root" --request POST http://localhost:8200/v1/auth/approle/role/transactions-role/secret-id)
secret_id=$(echo "${secret_id_response}" | jq -r '.data.secret_id')
echo "secret-id: $secret_id"
