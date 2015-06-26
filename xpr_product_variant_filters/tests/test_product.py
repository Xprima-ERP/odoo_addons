from openerp.tests.common import TransactionCase


class TestProduct(TransactionCase):
    def test_create_variant_ids(self):
        """
        Let super().create_variant_ids() do its things and then delete
        non logical variants
        """
        # #############First test case
        # Attributes creation
        attribute1 = self.env["product.attribute"].create({
            "name": "attribute1"
        })
        attribute2 = self.env["product.attribute"].create({
            "name": "attribute2"
        })

        # values creation
        attribute1_value1 = self.env["product.attribute.value"].create({
            "name": "attribute1_value_1",
            "attribute_id": attribute1.id
        })
        attribute1_value2 = self.env["product.attribute.value"].create({
            "name": "attribute1_value_2",
            "attribute_id": attribute1.id
        })
        attribute2_value1 = self.env["product.attribute.value"].create({
            "name": "attribute2_value_1",
            "attribute_id": attribute2.id
        })
        attribute2_value2 = self.env["product.attribute.value"].create({
            "name": "attribute2_value_2",
            "attribute_id": attribute2.id
        })

        # product.template creation
        template1 = self.env['product.template'].create({
            "name": "template1",
        })

        # attribute.line creation and association with template
        line_attr1 = self.env["product.attribute.line"].create({
            "attribute_id": attribute1.id,
            "value_ids": [(6, 0, [attribute1_value1.id, attribute1_value2.id])],
            "product_tmpl_id": template1.id
        })
        line_attr2 = self.env["product.attribute.line"].create({
            "attribute_id": attribute2.id,
            "value_ids": [(6, 0, [attribute2_value1.id, attribute2_value2.id])],
            "product_tmpl_id": template1.id
        })

        # Assign lines to template
        template1.write({
            "attribute_line_ids": [(6, 0, [line_attr1.id, line_attr2.id])]
        })

        # No filter created, the number of variants should be 0
        self.assertEqual(template1.product_variant_count, 0)

        # #############Second test case
        # product.template creation
        template2 = self.env['product.template'].create({
            "name": "template2",
        })

        # attribute.line creation and association with template
        line_attr1 = self.env["product.attribute.line"].create({
            "attribute_id": attribute1.id,
            "value_ids": [(6, 0, [attribute1_value1.id, attribute1_value2.id])],
            "product_tmpl_id": template2.id
        })
        line_attr2 = self.env["product.attribute.line"].create({
            "attribute_id": attribute2.id,
            "value_ids": [(6, 0, [attribute2_value1.id, attribute2_value2.id])],
            "product_tmpl_id": template2.id
        })

        # Create filters
        self.env["pvf.filter"].create({
            "template_id": template2.id,
            "product_attribute_value_ids": [
                (6, 0, [attribute1_value1.id, attribute2_value1.id])
            ]
        })
        self.env["pvf.filter"].create({
            "template_id": template2.id,
            "product_attribute_value_ids": [
                (6, 0, [attribute1_value1.id, attribute2_value2.id])
            ]
        })

        # Assign lines to template
        template2.write({
            "attribute_line_ids": [(6, 0, [line_attr1.id, line_attr2.id])]
        })

        # 2 Filters should permit 2 variants not 4
        self.assertEqual(template2.product_variant_count, 2)
