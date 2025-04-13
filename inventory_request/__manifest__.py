# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Inventory Requests',
    'version': '17.0.0.0.1',
    'author': 'ZooMTech Trading PLC',
    'depends': ['hr'],
    'description': """Manage All Requests""",
    'summary': 'Inventory Request Management',
    'category': 'Inventory',
    'sequence': 1,
    'website': 'https://zoometechet.com',
    'license': 'LGPL-3',
    'price': '80.0',
    'currency': 'USD',
    'images': ['static/description/assets.gif'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/local_purchase_request_sequence.xml',
        'views/local_purchase_order_views.xml',
        'views/receipt_views.xml',
        'views/payment_voucher_views.xml',
        'views/delivery_note_views.xml',
        'views/store_issue_voucher_views.xml',
        'views/good_receiving_note_views.xml',
        'views/material_requisition_note_views.xml',
        'views/purchase_order_requisition_views.xml',
        'views/warehouse.xml',
        'views/wood_flex_projects_views.xml',
        'views/production_transfer_views.xml',
        'views/supplier_list_views.xml',
        'reports/project_detail_report.xml',
        'reports/project_summary.xml',
        'reports/report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'woodflex_request/static/src/scss/account_asset.scss'
        ],
    },

    'application': True,
}
