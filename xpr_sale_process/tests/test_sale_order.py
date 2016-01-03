from openerp.exceptions import AccessError
from openerp.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    def test_has_rights_to_approve(self):
        """
        To have the right to approve or disapprove a quote, a user must be a
        manager and the salesperson associated to the quote he must approve
        must be uder him in the HR Odoo application.
        """
        so_customer = self.env['res.partner'].create({
            "name": "Test cie",
            "is_company": True,
        })

        so_owner_manager_partner = self.env['res.partner'].create({
            "name": "Test Manager",
            "email": "test_manager@xprima.com"
        })
        so_owner_manager = self.env['res.users'].create({
            "name": "Test Manager",
            "login": "test_manager@xprima.com",
            "groups_id": [(6, 0, [self.ref('base.group_sale_manager')])],
            "partner_id": so_owner_manager_partner.id,
        })

        so_owner_partner = self.env['res.partner'].create({
            "name": "Test Salesperson",
            "email": "test_salesperson@xprima.com"
        })
        so_owner = self.env['res.users'].create({
            "name": "Test Salesperson",
            "login": "test_salesperson@xprima.com",
            "groups_id": [(6, 0, [self.ref('base.group_sale_salesman')])],
            "partner_id": so_owner_partner.id,
        })

        hr_manager = self.env['hr.employee'].create({
            "name": "Test Manager",
            "user_id": so_owner_manager.id,
        })
        self.env['hr.employee'].create({
            "name": "Test Salesperson",
            "user_id": so_owner.id,
            "parent_id": hr_manager.id,
        })

        so1 = self.env['sale.order'].sudo(so_owner_manager).create({
            "name": "test_so1",
            "user_id": so_owner.id,
            "partner_id": so_customer.id,
        })
        # Test case if approver of so is so_owner_manager where he is the
        # manager of the owner
        self.assertTrue(so1.has_rights_to_approve())

        so2 = self.env['sale.order'].create({
            "name": "test_so2",
            "user_id": so_owner.id,
            "partner_id": so_customer.id,
        })
        # Test case if approver is admin. Admin is not owner's manager
        self.assertRaises(AccessError, so2.has_rights_to_approve)

    def test_product_availability_needed(self):
        """
        Test product.product.check_product_availability_needed()
        """
        so_customer = self.env['res.partner'].create({
            "name": "Test cie",
            "is_company": True,
        })

        so_owner_manager_partner = self.env['res.partner'].create({
            "name": "Test Manager",
            "email": "test_manager@xprima.com"
        })
        so_owner_manager = self.env['res.users'].create({
            "name": "Test Manager",
            "login": "test_manager@xprima.com",
            "groups_id": [(6, 0, [self.ref('base.group_sale_manager')])],
            "partner_id": so_owner_manager_partner.id,
        })

        so_owner_partner = self.env['res.partner'].create({
            "name": "Test Salesperson",
            "email": "test_salesperson@xprima.com"
        })
        so_owner = self.env['res.users'].create({
            "name": "Test Salesperson",
            "login": "test_salesperson@xprima.com",
            "groups_id": [(6, 0, [self.ref('base.group_sale_salesman')])],
            "partner_id": so_owner_partner.id,
        })
        availability_group = self.env["res.groups"].create({
            "name": "availability_group"
        })
        product1 = self.env['product.product'].create({
            "name": "test_product_availability_check_needed",
            "availability_groups": [(6, 0, [availability_group.id])]
        })
        so1 = self.env["sale.order"].create({
            "name": "so1",
            "user_id": so_owner.id,
            "partner_id": so_customer.id,
        })
        order_line1 = self.env["sale.order.line"].create({
            "name": "so1",
            "order_id": so1.id,
            "product_id": product1.id,
        })

        # Test case where availability group is set
        self.assertTrue(so1.check_product_availability_needed())

        product2 = self.env['product.product'].create({
            "name": "test_product_availability_check_needed2",
        })
        so2 = self.env["sale.order"].create({
            "name": "so2",
            "user_id": so_owner.id,
            "partner_id": so_customer.id,
        })
        order_line2 = self.env["sale.order.line"].create({
            "name": "so2",
            "order_id": so2.id,
            "product_id": product2.id,
        })

        # Test case where availability group is not set
        self.assertFalse(so2.check_product_availability_needed())
