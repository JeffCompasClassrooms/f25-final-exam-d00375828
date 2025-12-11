import pytest
from christmas_list import ChristmasList


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_christmas_list.pkl"


@pytest.fixture
def app(db_path):
    return ChristmasList(str(db_path))


def describe_christmas_list_system():

    # 1. INITIALIZATION & LOADING

    def it_creates_an_empty_list_if_file_missing(app):
        assert app.loadItems() == []

    # 2. ADDING ITEMS & PERSISTENCE

    def it_adds_items_and_persists_across_instances(app, db_path):
        app.add("socks")
        app.add("hat")

        new_app = ChristmasList(str(db_path))
        items = new_app.loadItems()

        names = [item["name"] for item in items]
        purchased_flags = [item["purchased"] for item in items]

        assert names == ["socks", "hat"]
        assert purchased_flags == [False, False]

    def it_handles_empty_item_name_gracefully(app):
        app.add("") 

        items = app.loadItems()
        assert len(items) in (0, 1)

    def it_allows_duplicate_item_names_as_separate_entries(app):
        app.add("socks")
        app.add("socks")

        items = app.loadItems()
        assert len(items) == 2
        assert all(i["name"] == "socks" for i in items)

    # 3. CHECKING OFF ITEMS

    def it_marks_items_purchased_and_reflects_in_print_output(app, db_path, capsys):
        app.add("socks")
        app.check_off("socks")

        new_app = ChristmasList(str(db_path))
        items = new_app.loadItems()
        assert items[0]["purchased"] is True

        new_app.print_list()
        captured = capsys.readouterr()
        assert "[x] socks" in captured.out

    def it_only_marks_one_item_as_purchased(app):
        app.add("socks")
        app.add("hat")

        app.check_off("socks")

        items = app.loadItems()
        socks = next(i for i in items if i["name"] == "socks")
        hat = next(i for i in items if i["name"] == "hat")

        assert socks["purchased"] is True
        assert hat["purchased"] is False

    def it_handles_unknown_item_names_without_crashing(app):
        app.add("socks")

        app.remove("not-there")
        app.check_off("not-there")

        items = app.loadItems()
        assert len(items) == 1
        assert items[0]["name"] == "socks"
        assert items[0]["purchased"] is False

    # 4. REMOVING ITEMS

    def it_removes_items_from_the_list(app, db_path):
        app.add("socks")
        app.add("hat")

        app.remove("socks")

        new_app = ChristmasList(str(db_path))
        names = [item["name"] for item in new_app.loadItems()]

        assert names == ["hat"]

    def it_can_remove_a_purchased_item(app, db_path):
        app.add("socks")
        app.check_off("socks")

        app.remove("socks")

        new_app = ChristmasList(str(db_path))
        items = new_app.loadItems()
        assert items == []

    def it_keeps_other_items_after_removing_one(app, db_path):
        app.add("socks")
        app.add("hat")
        app.check_off("hat")

        app.remove("socks")

        new_app = ChristmasList(str(db_path))
        items = new_app.loadItems()

        assert len(items) == 1
        assert items[0]["name"] == "hat"
        assert items[0]["purchased"] is True

    # 5. PRINTING BEHAVIOR

    def it_prints_nothing_when_list_is_empty(app, capsys):
        app.print_list()
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    def it_prints_unpurchased_items_with_underscore(app, capsys):
        app.add("hat")

        app.print_list()
        captured = capsys.readouterr()
        assert "[_] hat" in captured.out

    def it_prints_multiple_items_in_order(app, capsys):
        app.add("socks")
        app.add("hat")

        app.print_list()
        lines = capsys.readouterr().out.strip().splitlines()

        assert "[_] socks" in lines[0]
        assert "[_] hat" in lines[1]
