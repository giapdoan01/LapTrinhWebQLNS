import csv
import re
from datetime import datetime
from unidecode import unidecode
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from HOME.models import NhanVien, HopDongLaoDong, BHXH, NghiPhep, KyLuat, KhenThuong, ChamCong


class Command(BaseCommand):
    help = 'Load employee management data from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str)

    @staticmethod
    def convert_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            return None

    @staticmethod
    def generate_username(full_name):
        return unidecode(full_name).replace(" ", "").lower()

    @staticmethod
    def row_to_dict(row, header):
        if len(row) < len(header):
            row += [''] * (len(header) - len(row))
        return dict([(header[i], row[i]) for i, head in enumerate(header) if head])

    def handle(self, *args, **options):
        m = re.compile(r'content:\s*(\w+)')

        header = None
        models = dict()
        try:
            with open(options['csv'], encoding='utf-8-sig') as csvfile:
                model_data = csv.reader(csvfile)
                model_name = None
                for i, row in enumerate(model_data):
                    print(f"Row {i}: {row}")  # Debug
                    if max([len(cell.strip()) for cell in row[1:] + ['']]) == 0 and m.match(row[0]):
                        print(f"Detected model: {model_name}")  # Debug
                        model_name = m.match(row[0]).groups()[0]
                        models[model_name] = []
                        header = None
                        continue

                    if header is None:
                        header = row
                        continue
                    if model_name is None:
                        raise CommandError(f"Model name is missing or invalid in row {i}: {row}")

                    row_dict = self.row_to_dict(row, header)
                    if set(row_dict.values()) == {''}:
                        continue
                    models[model_name].append(row_dict)
        except FileNotFoundError:
            raise CommandError('File "{}" does not exist'.format(options['csv']))

        for data_dict in models.get('NhanVien', []):
            username = self.generate_username(data_dict['ten_nv'])
            user, created = User.objects.get_or_create(username=username, defaults={
                'first_name': data_dict['ten_nv'].split()[-1],
                'last_name': " ".join(data_dict['ten_nv'].split()[:-1]),
                'email': data_dict['email'],
                'is_staff': True,
                'is_active': True
            })
            user.set_password('123456789')
            user.save()

            nv, created = NhanVien.objects.get_or_create(user=user, defaults={
                'ten_nv': data_dict['ten_nv'],
                'so_cccd': data_dict['so_cccd'],
                'anh_ca_nhan' : data_dict['anh_ca_nhan'],
                'ngay_sinh': self.convert_date(data_dict['ngay_sinh']),
                'dia_chi': data_dict['dia_chi'],
                'so_dien_thoai': data_dict['so_dien_thoai'],
                'email': data_dict['email'],
                'trinh_do_hoc_van': data_dict['trinh_do_hoc_van'],
                'kinh_nghiem_lam_viec': int(data_dict['kinh_nghiem_lam_viec']),
                'vi_tri_cong_viec': data_dict['vi_tri_cong_viec']
            })

        for data_dict in models.get('HopDongLaoDong', []):
            HopDongLaoDong.objects.get_or_create(nhan_vien=NhanVien.objects.get(id=int(data_dict['nhan_vien'])),
                                                 loai_hop_dong=data_dict['loai_hop_dong'],
                                                 thoi_han_hop_dong=data_dict['thoi_han_hop_dong'],
                                                 ngay_vao_lam=self.convert_date(data_dict['ngay_vao_lam']),
                                                 muc_luong=float(data_dict['muc_luong']),
                                                 trang_thai_hop_dong=data_dict['trang_thai_hop_dong'])

        for data_dict in models.get('BHXH', []):
            BHXH.objects.get_or_create(nhan_vien=NhanVien.objects.get(id=int(data_dict['nhan_vien'])),
                                       ma_bhxh= data_dict['ma_bhxh'],
                                       thoi_gian_bat_dau_dong=self.convert_date(data_dict['thoi_gian_bat_dau']))

        for data_dict in models.get('KyLuat', []):
            KyLuat.objects.get_or_create(nhan_vien=NhanVien.objects.get(id=int(data_dict['nhan_vien'])),
                                         ngay_bat_dau=self.convert_date(data_dict['ngay_bat_dau']),
                                         muc_do=data_dict['muc_do'],
                                         ly_do=data_dict['ly_do'])

        for data_dict in models.get('KhenThuong', []):
            KhenThuong.objects.get_or_create(nhan_vien=NhanVien.objects.get(id=int(data_dict['nhan_vien'])),
                                             ngay_khen_thuong=self.convert_date(data_dict['ngay_khen_thuong']),
                                             gia_tri=float(data_dict['gia_tri']),
                                             ly_do=data_dict['ly_do'])

        for data_dict in models.get('NghiPhep', []):
            NghiPhep.objects.get_or_create(nhan_vien=NhanVien.objects.get(id=int(data_dict['nhan_vien'])),
                                           loai_nghi=data_dict['loai_nghi'],
                                           ngay_bat_dau=self.convert_date(data_dict['ngay_bat_dau']),
                                           ngay_ket_thuc=self.convert_date(data_dict['ngay_ket_thuc']),
                                           ly_do=data_dict['ly_do'],
                                           ngay_tao_don=self.convert_date(data_dict['ngay_tao_don']),
                                           trang_thai_don=data_dict['trang_thai_don'],
                                           ghi_chu=data_dict.get('ghi_chu', ''))

        for data_dict in models.get('ChamCong', []):
            ChamCong.objects.get_or_create(
                nhan_vien=NhanVien.objects.get(id=int(data_dict['id_nv'])),
                gio_vao=data_dict['gio_vao'] if data_dict['gio_vao'] else None,
                gio_ra=data_dict['gio_ra'] if data_dict['gio_ra'] else None,
                ngay=self.convert_date(data_dict['ngay']),
                trang_thai=int(data_dict['trang_thai'])
            )

        print("Import complete")