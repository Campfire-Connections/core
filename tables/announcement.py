import django_tables2 as tables


class AnnouncementsTable(tables.Table):
    title = tables.Column(verbose_name="Title")
    created_at = tables.DateColumn(verbose_name="Date Created")
    content = tables.Column(verbose_name="Content")

    class Meta:
        model = Announcement
        fields = ["title", "created_at", "content"]
