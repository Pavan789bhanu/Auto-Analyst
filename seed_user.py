"""
DEPRECATED — Prysm no longer uses a demo seed user.

Admin accounts are now provisioned the production way:

  1. Set these in backend/.env:
         ADMIN_USERNAME=admin
         ADMIN_EMAIL=admin@yourdomain.com
         ADMIN_PASSWORD=your-strong-password
     Then start the backend — the admin account is created/updated on boot.

  2. Or create one on demand with the CLI:
         cd backend
         flask --app app create-admin

Regular users can still self-register at /register in the web app.

Running this script just prints these instructions.
"""

if __name__ == "__main__":
    print(__doc__)
