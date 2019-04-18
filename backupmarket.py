import pathlib
import datetime
import playhouse.sqlite_ext

backups_path = pathlib.Path('./backups/')
backups_path.mkdir(exist_ok=True)
filename = backups_path / ('market-backup-%s.db' % (datetime.date.today()))

db = playhouse.sqlite_ext.CSqliteExtDatabase('market.db')
db.backup_to_file(str(filename))

