# Seasonal Specialty Product Marketplace

A small database application for a seasonal specialty product marketplace. The project was built for a database design lab and demonstrates the full workflow from requirement analysis and data modeling to MySQL implementation and a web-based frontend/backend application.

## Features

- User registration, login, logout, and role-based access.
- Product browsing, searching, category filtering, publishing, and off-sale removal.
- Favorites, shopping cart, wallet recharge, checkout, and order detail management.
- Seller center for shipping orders and replying to complaints.
- Complaint submission, administrator handling, optional refund processing, and user freezing.
- Chinese/English frontend language switch.
- MySQL view, index, trigger, and stored procedures.

## Tech Stack

- Backend: Flask + MySQL
- Frontend: HTML + Bootstrap + jQuery
- Database: MySQL
- Data modeling: PowerDesigner CDM, LDM, and PDM diagrams

## Project Structure

```text
.
├── app.py                  # Flask API server
├── db.py                   # MySQL connection helpers
├── init_db.py              # SQL initialization runner
├── seasonal_market.sql     # Database schema and database objects
├── frontend/
│   └── index.html          # Bootstrap + jQuery frontend
├── CDM.png                 # Conceptual Data Model diagram
├── LDM.png                 # Logical Data Model diagram
├── PDM.png                 # Physical Data Model diagram
├── test_db.py              # Database connection test
├── test_api.py             # Flask API smoke tests
├── requirements.txt
└── .env.example
```

## Database Design

The database contains eight core entities:

| Entity | Description |
| --- | --- |
| User | Stores ordinary users, sellers, administrators, account status, and wallet balance. |
| Category | Stores product category information. |
| Product | Stores product details, sale period, price, publisher, category, and sale status. |
| Order | Stores transaction order data and lifecycle status. |
| OrderItem | Stores products and quantities inside each order. |
| CartItem | Stores products added to a user's cart. |
| Favorite | Stores user favorite records. |
| Complaint | Stores complaints, seller replies, administrator opinions, and refund information. |

Main relationships include category-product, user-product, user-order, order-order item, product-order item, user-cart item, product-cart item, user-favorite, product-favorite, user-complaint, and order-complaint relationships.

## Database Objects

- View: `vw_product_details`
- Index: `idx_product_name`
- Trigger: `trg_update_product_status`
- Stored procedures:
  - `sp_handle_complaint`
  - `sp_confirm_receive`

## Setup

1. Clone the repository.

2. Create and activate a Python virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Copy the example environment file and update the MySQL password if needed.

```bash
copy .env.example .env
```

This project reads the following environment variables:

| Variable | Default |
| --- | --- |
| `MYSQL_HOST` | `localhost` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_DATABASE` | `seasonal_market` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | `root` |
| `MYSQL_CONNECT_TIMEOUT` | `3` |
| `SECRET_KEY` | `seasonal_market_secret_key_2026` |

5. Initialize the database.

```bash
python init_db.py
```

The SQL script creates the schema, tables, constraints, view, index, trigger, and stored procedures. It does not insert default test data.

6. Start the backend server.

```bash
python app.py
```

The backend runs on:

```text
http://localhost:5000
```

7. Start the frontend server in another terminal.

```bash
cd frontend
python -m http.server 8080
```

Open:

```text
http://localhost:8080
```

## API Modules

- Authentication: registration, login, logout, current user
- Products: list, search, detail, create, remove/off-sale
- Categories: list categories
- Cart: list, add, update quantity, remove, clear
- Orders: checkout, list, detail, confirm receipt
- Favorites: list, add, remove
- Complaints: list, create, handle
- Seller center: seller orders, shipping, seller complaint replies
- Admin panel: product supervision, complaint handling, user freezing
- Health check: `/api/health`

## Data Models

### CDM

![CDM](CDM.png)

### LDM

![LDM](LDM.png)

### PDM

![PDM](PDM.png)

## Notes

- Product removal is implemented as a status update (`product_status = 'off_sale'`) instead of physical deletion, so historical order data remains intact.
- The frontend API base URL follows the current hostname and targets backend port `5000`.
- The repository intentionally excludes virtual environments, IDE files, cache files, local `.env` files, and generated report output.
