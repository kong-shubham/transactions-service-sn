#!/bin/sh

export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root

vault secrets list | grep -q 'secret/' || vault secrets enable -path=secret kv

vault kv put secret/transactions-api/api-key value=super-secret-api-key

vault policy write transactions-policy - <<EOF
path "secret/data/transactions-api/*" {
  capabilities = ["read"]
}
EOF

vault auth list | grep -q 'approle/' || vault auth enable approle

vault write auth/approle/role/transactions-role \
  secret_id_ttl=60m \
  token_num_uses=0 \
  token_ttl=60m \
  token_max_ttl=120m \
  policies="transactions-policy"

vault read -field=role_id auth/approle/role/transactions-role/role-id > /vault/role_id.txt
vault write -f -field=secret_id auth/approle/role/transactions-role/secret-id > /vault/secret_id.txt

echo "Vault initialised with KV secret, policy, and AppRole."

