{
    "name": "Terms and Conditions",
    "version": "0.2",

    'summary': """
    The Xprimas port of Terms And Conditions
    """,

    "description": """
    Module that allows you to add custom pdf files to any report (e.g. Terms and Conditions)
    

==================================
WHAT CAN YOU DO WITH IT?
==================================
Add one or more pdf documents to any Odoo report!

    - Automatically have such attachment(s) included in your report.
    - Specify where you want the attachment(s) to be included in the report
        - Before the report
        - After the report
        - Every other page (e.g. for duplex printing)
    - Define your own conditions as to when the attachment should be included in the report 
    (e.g. only when checkbox Print Terms has been set to true for a partner)
    
Example: automatically attach your General Terms and Conditions to your Sales Invoices so that they are automatically printed for each invoice.

==================================
WHAT IS CHANGED IN ODOO?
==================================
The field Print Terms has been added to the Sales & Purchases tab of the Customer form. You can include this field in the attachment conditions.
The Settings --> Company menu has two new menu items:
- Terms
- Term Rules

==================================
WHAT DO YOU HAVE TO DO TO GET IT TO WORK?
==================================

In the Settings --> Companies menu, create at least one Term and Term Rule.

- Terms: to enter the name of your attachment, add the pdf file and select the Insertion mode (where the document should be included)

- Term Rules: to define for a specific Term the link from your pdf file to an Odoo report, e.g. Invoices (account.invoice).
  Add your conditions to determine when the attachment should be added to the report. If no condition specified, the attachment will
  always be included in the selected report.

==================================
Notice
==================================
This is an unofficial port of the version 7.0 of the agaplan_terms_and_conditions module.

    """,
    "category": "Generic Modules/Base",
    "author": "Xprima",
    "website": "http://www.agaplan.eu",
    "depends": [
        "base",
    ],
    "init": [],
    "update_xml": [
        'views/term_view.xml',
        'views/partner_view.xml',
        'security/ir.model.access.csv',
    ],
    "demo": [],
    "test": [],
    "installable": True,
}
# vim:sts=4:et
