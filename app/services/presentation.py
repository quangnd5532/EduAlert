"""Display names for legacy seeded text; never rewrite user-authored content."""
LEGACY_LABELS={
    'Bộ quy tắc minh họa phục vụ demo':'Đánh giá học tập chung',
    'Toán ứng dụng (giả lập)':'Toán ứng dụng',
    'Kỹ năng học thuật (giả lập)':'Kỹ năng học thuật',
    'THPT giả lập':'THPT',
    'Quản trị Demo':'Quản trị học vụ',
    'Ghi chú giả lập: đã trao đổi mục tiêu và thống nhất buổi theo dõi.':'Đã trao đổi mục tiêu và thống nhất buổi theo dõi.',
}


def display_text(value):
    return LEGACY_LABELS.get(value,value) if isinstance(value,str) else value
