#!/usr/bin/env python

from zope import interface

class IWSWillUpgradeEvent(interface.Interface):

	environ = interface.Attribute( "WSGI Environment dictionary" )

class IWSWillUpgradeVeto(interface.Interface):

	def can_upgrade(wswill_upgrade):
		"""
		:param wswill_upgrade: An :class:IWSWillUpgradeEvent.
		:return: Boolean indicating whether the event should upgrade.
		"""
