MADST
========

Multi Active Directory Sync Tool is an application developed for Managed Service Providers a mechanism to do the following.

 * Manage individual user accounts for each tech on customer AD systems (CRUD)
 * Updating user headcount totals for each customer organization in order to programmatically update agreements
 * Allow technicians to perform a password reset on all their associated accounts from one location


Status
======

What is done:

 * Server backend and client API
 * Primitive user interface

What isn't done:

 * Client interface
 * Syncing password hashes directly

Dependencies:

 * flask
 * flask-login
 * flask-sqlalchemy
 * wtforms
 * requests
 * sqlalchemy-migrate
 * pycrypto
 * ldap3
 
 Demo video here: https://www.youtube.com/watch?v=L7E6_daTmD8
