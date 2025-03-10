# tenantisolation
Tenant isolation in Django.

Tenant isolation allows secure data separation in a multi-tenant environment, ensuring that each client's data remains private and inaccessible to others.  

Each user has an account and a selected company account object. The objects whose models are derived from the TenantCoreModel will be isolated,
so users from Company A will not be able to see objects that belong to Company B.


To make messages, use:  
`django-admin makemessages -l tr -i venv`

To compile messages, use:  
`django-admin compilemessages`

To launch the application, use:   
`gunicorn tenantisolation.wsgi --bind 127.0.0.1:8000`

## VSCode Launch Configurations

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