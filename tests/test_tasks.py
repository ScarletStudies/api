from ssapi.tasks import add


def test_example_job(app):
    with app.app_context():
        job = add.queue(1, 2)
        assert job.result == 3
