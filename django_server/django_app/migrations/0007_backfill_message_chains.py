from django.db import migrations


def link_existing_messages_into_chains(apps, schema_editor):
    """Pre-branching data was a flat, created_at-ordered list per chat — link
    it into a single linear chain (each message's parent is the one before
    it) and point active_leaf at the end, so get_active_path() returns
    exactly what was there before for every chat that predates branching.
    """
    ChatHistory = apps.get_model("django_app", "ChatHistory")
    ChatMessage = apps.get_model("django_app", "ChatMessage")

    for chat in ChatHistory.objects.all():
        previous = None
        for message in ChatMessage.objects.filter(chat=chat).order_by("created_at", "id"):
            if message.parent_id != (previous.id if previous else None):
                message.parent = previous
                message.save(update_fields=["parent"])
            previous = message

        if previous is not None and chat.active_leaf_id != previous.id:
            chat.active_leaf = previous
            chat.save(update_fields=["active_leaf"])


def noop_reverse(apps, schema_editor):
    # Nothing to undo — unlinking parents would just recreate the flat shape
    # get_messages_for_chat used to read directly from created_at order.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0006_message_branching"),
    ]

    operations = [
        migrations.RunPython(link_existing_messages_into_chains, noop_reverse),
    ]
