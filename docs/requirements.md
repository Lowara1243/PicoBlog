# PicoBlog Project Requirements

## Overall Goal
Create an alternative to WriteFreely, focused on performance and simplicity, without federation features.

## Key Features

### 1. Access and User Management
*   **Registration and Permissions:** Only the administrator can register new users and assign permissions.
*   **Read Access Control:** The administrator can specify tags; posts with these tags are accessible only to authorized users. Users will only see posts with tags allowed to them.

### 2. Content Upload
*   Ability to upload content (text, images) directly from the browser, without the need for additional applications.

### 3. Performance
*   The application must be performant enough to run on a Raspberry Pi, considering that content will consist primarily of text and images.

### 4. Content Creation
*   Fast content creation using Markdown.
*   Server-side rendering of Markdown to HTML/CSS.

### 5. Modern and Minimalist Design
*   Modern but minimalist appearance without using heavy frameworks (e.g., React).
*   Preference for TailwindCSS for styling.
*   Blog viewing pages should contain minimal JavaScript (ideally none). JavaScript is allowed for login pages and administrative interfaces.

### 6. Comments
*   Ability to leave comments on posts.
*   Markdown support within comments (with server-side rendering and mandatory sanitization).

### 7. Technical Details
*   **Database:** SQLite for data storage (e.g., information about posts, users, tags, comments).
*   **Markdown Rendering:** Performed on the server side for both posts and comments.
*   **Web Server:** Nginx as a reverse proxy, especially for providing HTTPS.
*   **Post Filtering:** Ability to filter posts on the backend based on tags available to the user.
