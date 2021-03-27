from pymodm import fields, MongoModel


class FileModel(MongoModel):
    fileId = fields.CharField(primary_key=True, required=True)
    processingStatus = fields.CharField(required=True)
    fileName = fields.CharField(required=True)
    fileLength = fields.IntegerField(required=False)
    mp3Path = fields.URLField(required=False)
    originalFilePath = fields.URLField(required=False)
    seriesTitle = fields.CharField(required=False)
    segments = fields.ListField(field=fields.DictField(), required=False)
