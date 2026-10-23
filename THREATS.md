# TrustVault Threat Model

## 1. Purpose and Scope

TrustVault supports user login, document uploads, document sharing, administrative user management, and an audit history. This document identifies important security risks and the tests needed to evaluate them.

The test results must be updated only after the tests have actually been performed.

## 2. Assets to Protect

- Uploaded documents.
- User accounts and password hashes.
- Document-sharing permissions.
- Administrative functions.
- Audit records.
- Flask session and secret key.
- SQLite database and stored files.

## 3. Threats and Mitigations

### Threat 1: Unauthorized Document Download

**Risk:** A logged-in user attempts to download a document they do not own and have not been given permission to access.

**Intended mitigation:** The server checks the current user's role, document ownership, and sharing permissions before returning a file.

**Verification test:**
1. Create two ordinary users, User A and User B.
2. Upload a document as User A.
3. Do not share it with User B.
4. Log in as User B and request the document's download URL directly.
5. Confirm the response denies access and does not return the document contents.
6. Check whether the denied attempt is recorded in the audit history.

**Status:** Not yet verified by a dedicated authorization test.

### Threat 2: Insecure Direct Object Reference (IDOR)

**Risk:** A user changes a document ID in a URL to attempt to access another user's document.

**Intended mitigation:** Every download request must independently check authorization for the requested document ID. Hiding a download link in the interface is not sufficient.

**Verification test:** While logged in as a user without permission, change the document ID in a download URL to another existing document's ID. Confirm that access is denied and no file contents are returned.

**Status:** Not yet verified by a dedicated IDOR test.

### Threat 3: Unauthorized Document Sharing

**Risk:** An ordinary user attempts to access an administrative sharing function or grants permissions without authorization.

**Intended mitigation:** The server checks that the current user is an administrator before processing administrative sharing requests.

**Verification test:** Log in as an ordinary user and attempt to access the sharing route directly. Confirm that the server rejects the request and does not create a permission record.

**Status:** Not yet verified by a dedicated authorization test.

### Threat 4: Password or Session Compromise

**Risk:** Weak passwords, leaked secrets, or insecure session configuration could allow account impersonation.

**Intended mitigation:** Passwords should be stored as hashes, and Flask should use a strong secret key provided through an environment variable.

**Verification steps:**
- Inspect the database to confirm passwords are not stored as plaintext.
- Confirm the production `TRUSTVAULT_SECRET_KEY` is set and is not committed to Git.
- Review session-cookie security settings and login/logout behavior.

**Status:** Requires further verification.

### Threat 5: Audit Log Gaps or Tampering

**Risk:** Important actions or denied access attempts are not recorded, or users can modify audit records.

**Intended mitigation:** The application records relevant actions on the server and restricts access to audit history.

**Verification test:**
1. Upload a document.
2. Share it with another user.
3. Perform an allowed download.
4. Attempt a denied download.
5. Review the audit history and check which events were recorded.
6. Verify that an ordinary user cannot access the administrative audit page.

**Status:** The audit history page was manually checked, but complete event coverage and tamper resistance have not been verified.

### Threat 6: Malicious or Oversized Uploads

**Risk:** An attacker uploads an oversized file or a file type that the application should not accept.

**Existing configuration:** The application sets a maximum request size of 10 MB.

**Verification steps:**
- Test an upload within the size limit.
- Test a file larger than the limit and confirm it is rejected.
- Review whether file types are restricted and whether filenames are handled safely.

**Status:** The size limit is configured; upload rejection and file-type handling require testing.

### Threat 7: Cross-Site Scripting (XSS)

**Risk:** User-controlled names or document metadata are inserted into HTML without appropriate escaping.

**Verification steps:** Review all templates and HTML responses that display user-controlled values. Confirm that the framework escapes these values rather than interpreting them as executable HTML or JavaScript.

**Status:** Requires code review and testing.

### Threat 8: Loss of Stored Documents and Database Records

**Risk:** Local files and SQLite records may disappear after a hosting restart or redeployment when the host uses ephemeral storage.

**Mitigation:** Use persistent storage and database backups for a production deployment.

**Status:** Known limitation of the current demonstration deployment.

## 4. Testing Record

No test should be marked as passed until its result has been observed.

| Test | Result |
|---|---|
| Login and main interface | Manually checked |
| User management | Manually checked |
| Document sharing | Manually checked |
| Audit history page | Manually checked |
| Unauthorized download | Not yet verified |
| IDOR attempt | Not yet verified |
| Non-admin access to admin routes | Not yet verified |
| Oversized upload rejection | Not yet verified |
| Automated test suite | Not yet completed |

## 5. Next Steps

1. Run the authorization tests using separate test accounts.
2. Verify that denied requests do not return document contents.
3. Check that audit records are generated for relevant events.
4. Review HTML escaping, session configuration, and upload handling.
5. Add automated tests and update this document with actual results.
6. Use persistent database and file storage before storing real confidential documents.
