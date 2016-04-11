# -*- coding: utf-8 -*-
from AccessControl.ZopeGuards import guarded_getattr
from Acquisition import aq_base
from DateTime import DateTime
from logging import exception
from plone.namedfile.interfaces import IAvailableSizes
from plone.namedfile.interfaces import IStableImageScale
from plone.namedfile.utils import set_headers
from plone.namedfile.utils import stream_data
from plone.rfc822.interfaces import IPrimaryFieldInfo
from plone.scale.scale import scaleImage
from plone.scale.storage import AnnotationStorage
from Products.Five import BrowserView
from xml.sax.saxutils import quoteattr
from ZODB.POSException import ConflictError
from zope.app.file.file import FileChunk
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound
from zope.traversing.interfaces import ITraversable
from zope.traversing.interfaces import TraversalError
from zope.interface import implements

import pkg_resources

from plone.namedfile.scaling import ImageScaling as NImageScaling 
from plone.namedfile.scaling import ImageScale as NImageScale 
from plone.namedfile.scaling import ImmutableTraverser

from plone import api
from collective.lazysizes.interfaces import ILazySizesSettings


try:
    pkg_resources.get_distribution('plone.protect>=3.0')
except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
    IDisableCSRFProtection = None
else:
    # Soft dependency to make this package work without plone.protect
    from plone.protect.interfaces import IDisableCSRFProtection

_marker = object()

class ImageScale(NImageScale):
    """ view used for rendering image scales """

    # Grant full access to this view even if the object being viewed is
    # protected
    # (it's okay because we explicitly validate access to the image attribute
    # when we retrieve it)
    __roles__ = ('Anonymous',)
    __allow_access_to_unprotected_subobjects__ = 1

        
    def tag(self, height=_marker, width=_marker, alt=_marker,
            css_class=None, title=_marker, **kwargs):
        """Create a tag including scale
        """
        if height is _marker:
            height = getattr(self, 'height', self.data._height)
        if width is _marker:
            width = getattr(self, 'width', self.data._width)

        if alt is _marker:
            alt = self.context.Title()
        if title is _marker:
            title = self.context.Title()

        #this part is used for lazyloading
        #there are more values than the original scaling.py   
        #we can probably check for blacklist here, 
        #the same we can do with sizes not enabled in control panel           

        #get settings, I think blacklist should be tuple
        
        blacklist    = api.portal.get_registry_record('collective.lazysizes.interfaces.ILazySizesSettings.css_class_blacklist')
        image_candidates = api.portal.get_registry_record('collective.lazysizes.interfaces.ILazySizesSettings.image_candidates')
        use_thumb = api.portal.get_registry_record('collective.lazysizes.interfaces.ILazySizesSettings.use_thumb')

        small_image = self.url

        #need to find which scale was used, can not find it anywere
        #the scale is present in the html, not sure where they got it from
        #so we could replace src and data-src in transform.py if everything else fails.
        #scale= 'large'
        
        # 'not in' is probably not good enough, will 'equal' classes that are partly the same (?) 
        # using tuple or list in control panel might be better ?       
        if not css_class:
            css_class = '  '
            
        item_url = self.context.absolute_url() 

        if css_class not in str(blacklist):
            css_class += ' lazyload'
            portal_url = api.portal.get().absolute_url()
            small_image =  portal_url + "/++resource++collective.lazysizes/blank.png"

            if use_thumb:
                small_image = item_url + '/@@images/' + self.fieldname + '/thumb'   
            
        #not sure if we should add  this to all images, or maybe use a 'retina' setting
        #maybe we coould use a list and 'move every size up a scale mini 1x => preview 2x
        base_url = item_url + '/@@images/' + self.fieldname 
        sizes = "(min-width: 1000px) 768px, 90vw"
        data_srcset = base_url + "/preview  400w, " + base_url +  "/large 640w, "

        values = [
            ('src', small_image),
            ('data-fieldname', self.fieldname),   
            ('sizes', sizes),        
            ('data-src', self.url),
            ('data-srcset', data_srcset),
            ('alt', alt),
            ('title', title),
            ('height', height),
            ('width', width),
            ('class', css_class),
        ]
        values.extend(kwargs.items())

        parts = ['<img']
        for k, v in values:
            if v is None:
                continue
            if isinstance(v, int):
                v = str(v)
            elif isinstance(v, str):
                v = unicode(v, 'utf8')
            parts.append(u'{0}={1}'.format(k, quoteattr(v)))
        parts.append('/>')
        
        return u' '.join(parts)


class ImageScaling(NImageScaling):
    """ view used for generating (and storing) image scales """
    # Ignore some stacks to help with accessing via webdav, otherwise you get a
    # 404 NotFound error.
    _ignored_stacks = ('manage_DAVget', 'manage_FTPget')

    def publishTraverse(self, request, name):
        """ used for traversal via publisher, i.e. when using as a url """
        stack = request.get('TraversalRequestNameStack')
        image = None
        if stack and stack[-1] not in self._ignored_stacks:
            # field and scale name were given...
            scale = stack.pop()
            image = self.scale(name, scale)             # this is aq-wrapped
        elif '-' in name:
            # we got a uid...
            if '.' in name:
                name, ext = name.rsplit('.', 1)
            storage = AnnotationStorage(self.context)
            info = storage.get(name)
            if info is not None:
                scale_view = ImageScale(self.context, self.request, **info)
                alsoProvides(scale_view, IStableImageScale)
                return scale_view.__of__(self.context)
        else:
            # otherwise `name` must refer to a field...
            if '.' in name:
                name, ext = name.rsplit('.', 1)
            value = getattr(self.context, name)
            scale_view = ImageScale(
                self.context, self.request, data=value, fieldname=name)
            return scale_view.__of__(self.context)
        if image is not None:
            return image
        raise NotFound(self, name, self.request)


    def scale(self,
              fieldname=None,
              scale=None,
              height=None,
              width=None,
              direction='thumbnail',
              **parameters):
        if fieldname is None:
            fieldname = IPrimaryFieldInfo(self.context).fieldname
        if scale is not None:
            available = self.getAvailableSizes(fieldname)
            if scale not in available:
                return None
            width, height = available[scale]

        if IDisableCSRFProtection and self.request is not None:
            alsoProvides(self.request, IDisableCSRFProtection)

        storage = AnnotationStorage(self.context, self.modified)
        info = storage.scale(factory=self.create,
                             fieldname=fieldname,
                             height=height,
                             width=width,
                             direction=direction,
                             **parameters)

        if info is not None:
            info['fieldname'] = fieldname
            scale_view = ImageScale(self.context, self.request, **info)
            return scale_view.__of__(self.context)


