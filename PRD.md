# PRD: DocSPARROW

## 1. Project Overview
**Role:** Senior Full Stack Django Developer
**Project Goal:** Build a centralized management system to track and visualize product documentation (Artifacts) across various categories and products. The UI must strictly replicate a grid-based matrix layout where users can view version statuses, manage file histories, and download assets via a centralized dashboard.

## 2. Tech Stack
- **Backend:** Python 3.x, Django 5.x
- **Database:** PostgreSQL
- **Frontend:** Django Templates, Tailwind CSS (via CDN), FontAwesome 6 (Icons), Alpine.js (for Modal/Popup interaction)
- **File Storage:** Local Media Storage

## 3. Matrix Configuration

### Rows (17 Document Categories)
1. 제품소개서
2. 브로슈어
3. 사례집(Use-CASE)
4. 제품비교표
5. 기능비교자료
6. BM비교자료
7. 시장점유율
8. 설치가이드
9. 사용설명서
10. 사용가이드
11. 관리자가이드
12. 규격서
13. 릴리즈노트
14. 사업계획서
15. 컴플라이언스/가이드
16. 인증서
17. 특허정보

### Columns (10 Products & Color Mapping)
- **Enterprise:** `bg-green-500`
- **SAST:** `bg-red-500`
- **SAQT:** `bg-indigo-600`
- **DAST:** `bg-orange-500`
- **SCA:** `bg-yellow-500`
- **P-Cloud:** `bg-blue-500`
- **G-Cloud:** `bg-green-600`
- **SecureHub:** `bg-blue-600`
- **On-Demand:** `bg-teal-500`
- **MCP:** `bg-purple-500`

## 4. Functional Requirements

### 4.1. Dashboard & Matrix View
- **Grid Layout:** Columns represent Products; Rows represent Document Categories.
- **Sticky Headers:** Top row (Product names/versions) and leftmost column (Categories) must be sticky for easy navigation.
- **Version Dropdown:** Each product header must have a dropdown to select a "Target Version" to compare against artifacts.

### 4.2. Artifact Card Logic
- **Empty State:** If no artifact is registered for a cell, show a light grey "Sad Face" icon (`fa-regular fa-face-frown`).
- **Filled State:** Show a white card containing:
    - `{Product Name} {Asset Version}`
    - Status Icon (Check for match, Warning for mismatch).
    - `{Category Name}`
- **Comparison Logic:**
    - **Match (Green):** `Asset Version` == `Selected Product Version`. Show `fa-check`.
    - **Mismatch (Red):** `Asset Version` < `Selected Product Version`. Show `fa-triangle-exclamation` and red text.

### 4.3. History & Management Popup (Modal)
- **Trigger:** Clicking on an active artifact card opens a Modal.
- **Features:**
    - **History List:** A table showing all previously uploaded versions for that specific product/category.
    - **Columns in Table:** Registration Date, Registered By (User), Version Number, File Name.
    - **CRUD Actions:**
        - **Upload:** Form to upload a new file and specify the version.
        - **Download:** Click to download specific historical files.
        - **Delete:** Remove a specific version entry (Admin only).

## 5. Database Schema Implementation Guide

1. **Product:** `name`, `color_hex`, `display_order`.
2. **ProductVersion:** `product` (FK), `version_number` (e.g., "2512.2"), `is_active`.
3. **Category:** `name`, `display_order`.
4. **Artifact:** - `product` (FK), `category` (FK)
    - `file` (FileField)
    - `version_string` (e.g., "5.18.0")
    - `uploader` (FK to User)
    - `created_at` (DateTimeField)

## 6. UI/Design Specifications
- **Reference Image Replicaton:** Use white cards with `shadow-sm`, rounded corners, and clear status indicators.
- **Interactivity:** Use Alpine.js to handle the modal state and version switching without full page reloads where possible.
- **Responsiveness:** Ensure the grid handles horizontal overflow gracefully (horizontal scroll).

## 7. Development Steps
1. **Setup:** Django project + PostgreSQL config.
2. **Models:** Implement the 4 core models defined in section 5.
3. **Admin:** Register all models to enable manual data management.
4. **Views:** Logic to fetch the latest artifact per category/product and compare it with the selected version.
5. **Templates:**
    - `base.html`: Tailwind/FontAwesome setup.
    - `index.html`: Main grid logic with nested loops.
    - `history_modal.html`: The AJAX-powered or Alpine.js modal for history and uploads.