#!/usr/bin/env python2.7

from zope import interface

class IWSWillUpgradeEvent(interface.Interface):

	environ = interface.Attribute( "WSGI Environment dictionary" )

class IWSWillUpgradeVeto(interface.Interface):

	def can_upgrade(wswill_upgrade):
		"""
		:param wswill_upgrade: An :class:IWSWillUpgradeEvent.
		:return: Boolean indicating whether the event should upgrade.
		"""
