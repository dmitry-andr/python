from app.domain.customer import Customer
from app.dao.customer_dao import CustomerDAO


def test_customer_dao_round_trip(tmp_path):
    db_path = tmp_path / "customers.db"

    dao = CustomerDAO(db_path=db_path)
    customer = Customer(first_name="Alice", last_name="Smith", email="alice@example.com")

    dao.save_customer(customer)
    saved = dao.list_customers()

    assert len(saved) == 1
    assert saved[0].first_name == "Alice"
    assert saved[0].email == "alice@example.com"


def test_customer_dao_update_customer(tmp_path):
    db_path = tmp_path / "customers.db"
    dao = CustomerDAO(db_path=db_path)

    customer = Customer(first_name="Alice", last_name="Smith", email="alice@example.com")
    dao.save_customer(customer)

    updated = Customer(
        id=customer.id,
        first_name="Alicia",
        last_name="Jones",
        phone="555-7777",
    )
    dao.update_customer(updated)

    saved = dao.get_customer_by_id(customer.id)
    assert saved is not None
    assert saved.first_name == "Alicia"
    assert saved.last_name == "Jones"
    assert saved.email is None
    assert saved.phone == "555-7777"
