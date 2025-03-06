# tenantisolation
Tenant isolation in Django.

Tenant isolation allows secure data separation in a multi-tenant environment, ensuring that each client's data remains private and inaccessible to others.  

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
    "cwd": "${workspaceFolder}/sirketim",
    "program": "${workspaceFolder}/sirketim/manage.py",
    "args": [
        "runserver",
        "8005"
    ],
    "django": true,
    "justMyCode": false,
},
```

***