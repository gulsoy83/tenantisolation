# tenantisolation
Tenant isolation in Django.

Tenant isolation allows secure data separation in a multi-tenant environment, ensuring that each client's data remains private and inaccessible to others.  

Each user has an account and a selected company account object. The objects whose models are derived from the TenantCoreModel will be isolated,
so users from Company A will not be able to see objects that belong to Company B.  
**Note:** Isolation can also be enabled in the admin panel.

## Examples
![mgcompany_isselected](https://github.com/user-attachments/assets/d136718a-8a85-4006-be1b-e1723e2cdc9a)  
Currently, the MG Company is selected.

![admin_isolation_off](https://github.com/user-attachments/assets/a7b5d678-d6ea-40f3-b4f8-2e778719bb66)  
All objects in the database. (admin_isolation_off)

![expensetypelist](https://github.com/user-attachments/assets/e24529d8-a369-4587-be17-38ccdbbbdba4)  
The expense type list, which, as you can see, is isolated.

![queryexample](https://github.com/user-attachments/assets/0bf80c48-8029-495e-86e2-cbf409612bf6)  
Query format.

### Notes

To make messages, use:  
`django-admin makemessages -l tr -i venv`

To compile messages, use:  
`django-admin compilemessages`

To launch the application, use:   
`gunicorn tenantisolation.wsgi --bind 127.0.0.1:8000`

#### VSCode Launch Configurations

```
{  
    "name": "Python: Django",
    "type": "python",
    "request": "launch",
    "cwd": "${workspaceFolder}/tenantisolation",
    "program": "${workspaceFolder}/tenantisolation/manage.py",
    "args": [
        "runserver",
        "8000"
    ],
    "django": true,
    "justMyCode": false,
},
```

***
