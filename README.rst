********************
collective.lazysizes
********************

.. contents:: Table of Contents

Life, the Universe, and Everything
==================================

This package integrates `lazysizes`_, a lightweight lazy loader, into Plone.

`lazysizes`_ is a fast, SEO-friendly and self-initializing lazyloader for images (including responsive images picture/srcset), iframes, scripts/widgets and much more.
It also prioritizes resources by differentiating between crucial in view and near view elements to make perceived performance even faster.

By using this package you can expect reductions of up to 80% in load time, 75% in page size and 50% in number of requests.

Mostly Harmless
===============

.. image:: http://img.shields.io/pypi/v/collective.lazysizes.svg
   :target: https://pypi.python.org/pypi/collective.lazysizes

.. image:: https://img.shields.io/travis/collective/collective.lazysizes/master.svg
    :target: http://travis-ci.org/collective/collective.lazysizes

.. image:: https://img.shields.io/coveralls/collective/collective.lazysizes/master.svg
    :target: https://coveralls.io/r/collective/collective.lazysizes

These are some sites using ``collective.lazysizes``:

* `CartaCapital <http://www.cartacapital.com.br/>`_ (BR)
* `Conversa Afiada <http://www.conversaafiada.com.br/>`_ (BR)
* `Portal Brasil 2016 <http://www.brasil2016.gov.br/>`_ (BR)

Got an idea? Found a bug? Let us know by `opening a support ticket <https://github.com/collective/collective.lazysizes/issues>`_.

Don't Panic
===========

Installation
------------

To enable this package in a buildout-based installation:

#. Edit your buildout.cfg and add add the following to it::

    [buildout]
    ...
    eggs =
        collective.lazysizes

After updating the configuration you need to run ''bin/buildout'', which will take care of updating your system.

Go to the 'Site Setup' page in a Plone site and click on the 'Add-ons' link.

Check the box next to ``collective.lazysizes`` and click the 'Activate' button.

.. Note::
    You may have to empty your browser cache and save your resource registries in order to see the effects of the product installation.

How does it work
----------------

This package adds a transform to the transform chain to integrate `lazysizes`_ into Plone.

The transform looks for all the ``<img>`` and ``<iframe>`` elements inside the content and does the following:

* appends a ``lazyload`` class
* transforms the ``src`` attribute into a ``data-src`` attribute
* if the element is an ``<img>``, uses an spinner as ``src`` attribute (this is done to maintain valid HTML code)

The transform is only applied to anonymous users.

As long as `we have tested <https://github.com/aFarkas/lazysizes/issues/239>`_, `lazysizes`_ seems not to interfere with image indexing made by crawlers like Googlebot.

Todo
----

* implement support for responsive images with ``srcset`` and automatic ``sizes`` attribute

.. _`lazysizes`: https://afarkas.github.io/lazysizes/
