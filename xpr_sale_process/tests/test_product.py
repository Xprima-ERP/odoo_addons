from openerp.tests.common import TransactionCase


# class TestProduct(TransactionCase):
#     def test_approver_group(self):

#         product_name = "Test Product"
#         approver_group_name = "Approver Group"

#         approver_group = self.env["res.groups"].create({
#             "name": approver_group_name
#         })

#         product = self.env['product.template'].create({
#             "name": product_name,
#             "approver_groups": [(6, 0, [approver_group.id])]
#         })

#         self.assertEqual(product.approver_groups[0].name, approver_group_name)
