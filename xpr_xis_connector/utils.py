# -*- encoding: utf-8 -*-
def set_xis_fqdn(obj_with_url, oe_orm_obj, cr, uid, context):
    '''
    Set the url property of a given object if the xis_fqdn config param is
    specified in an OpenERP instance. This is usefull for testing purpose
    since the url for xis is not always the same from different network.
    '''
    # Check if xis url is specified as config param.
    conf_param_obj = oe_orm_obj.pool.get('ir.config_parameter')
    param_ids = conf_param_obj.search(cr,
                                      uid,
                                      [('key', '=', 'xis_fqdn')],
                                      context=context)
    if param_ids:
        param_id = param_ids[0]
        xis_fqdn_param = conf_param_obj.browse(cr, uid, param_id, context)
        xis_fqdn = xis_fqdn_param.value
        obj_with_url.url = 'http://%s/ws/dealers_sf.spy' % xis_fqdn
