# Jimmy on Azure

Public Container App with **4 independent password logins** (`jimmy1`–`jimmy4`), shared Azure OpenAI, isolated profiles (sessions + Telegram).

## Live URL

https://ca-jimmy-yd6h7x5ni6ki4.braveriver-d2909cea.eastus.azurecontainerapps.io/chat

Login: https://ca-jimmy-yd6h7x5ni6ki4.braveriver-d2909cea.eastus.azurecontainerapps.io/login

Resource group: `rg-jimmy-eastus`  
Portal: https://portal.azure.com/#@/resource/subscriptions/ef27ac90-4a8e-4d2d-8de0-22d1924f023e/resourceGroups/rg-jimmy-eastus

## Credentials

Passwords are in `.azure/jimmy-credentials.local.txt` (gitignored). Log in with:

| Username | Profile |
|----------|---------|
| jimmy1 | jimmy1 |
| jimmy2 | jimmy2 |
| jimmy3 | jimmy3 |
| jimmy4 | jimmy4 |

## Redeploy image

```powershell
az acr build --registry jimmyyd6h7x5ni6ki4 --image jimmy:latest --file Dockerfile .
az containerapp update -g rg-jimmy-eastus -n ca-jimmy-yd6h7x5ni6ki4 `
  --image jimmyyd6h7x5ni6ki4.azurecr.io/jimmy:latest
```

## Isolation

- Auth session claims `profile`; middleware forces `?profile=` and returns 403 on mismatch.
- Profile switcher is locked for bound users.
- `gateway.multiplex_profiles` + per-profile `HERMES_HOME/profiles/jimmyN`.
