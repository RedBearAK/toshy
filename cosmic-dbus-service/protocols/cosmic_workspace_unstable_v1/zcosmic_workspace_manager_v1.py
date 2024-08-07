# This file has been autogenerated by the pywayland scanner

# Copyright © 2019 Christopher Billington
# Copyright © 2020 Ilia Bozhinov
# Copyright © 2022 Victoria Brekenfeld
#
# Permission to use, copy, modify, distribute, and sell this
# software and its documentation for any purpose is hereby granted
# without fee, provided that the above copyright notice appear in
# all copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# the copyright holders not be used in advertising or publicity
# pertaining to distribution of the software without specific,
# written prior permission.  The copyright holders make no
# representations about the suitability of this software for any
# purpose.  It is provided "as is" without express or implied
# warranty.
#
# THE COPYRIGHT HOLDERS DISCLAIM ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS, IN NO EVENT SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY
# SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
# AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
# ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
# THIS SOFTWARE.

from __future__ import annotations

from pywayland.protocol_core import (
    Argument,
    ArgumentType,
    Global,
    Interface,
    Proxy,
    Resource,
)

from .zcosmic_workspace_group_handle_v1 import ZcosmicWorkspaceGroupHandleV1


class ZcosmicWorkspaceManagerV1(Interface):
    """List and control workspaces

    Workspaces, also called virtual desktops, are groups of surfaces. A
    compositor with a concept of workspaces may only show some such groups of
    surfaces (those of 'active' workspaces) at a time. 'Activating' a workspace
    is a request for the compositor to display that workspace's surfaces as
    normal, whereas the compositor may hide or otherwise de-emphasise surfaces
    that are associated only with 'inactive' workspaces. Workspaces are grouped
    by which sets of outputs they correspond to, and may contain surfaces only
    from those outputs. In this way, it is possible for each output to have its
    own set of workspaces, or for all outputs (or any other arbitrary grouping)
    to share workspaces. Compositors may optionally conceptually arrange each
    group of workspaces in an N-dimensional grid.

    The purpose of this protocol is to enable the creation of taskbars and
    docks by providing them with a list of workspaces and their properties, and
    allowing them to activate and deactivate workspaces.

    After a client binds the :class:`ZcosmicWorkspaceManagerV1`, each workspace
    will be sent via the workspace event.
    """

    name = "zcosmic_workspace_manager_v1"
    version = 2


class ZcosmicWorkspaceManagerV1Proxy(Proxy[ZcosmicWorkspaceManagerV1]):
    interface = ZcosmicWorkspaceManagerV1

    @ZcosmicWorkspaceManagerV1.request()
    def commit(self) -> None:
        """All requests about the workspaces have been sent

        The client must send this request after it has finished sending other
        requests. The compositor must process a series of requests preceding a
        commit request atomically.

        This allows changes to the workspace properties to be seen as atomic,
        even if they happen via multiple events, and even if they involve
        multiple
        :class:`~pywayland.protocol.cosmic_workspace_unstable_v1.ZcosmicWorkspaceHandleV1`
        objects, for example, deactivating one workspace and activating
        another.
        """
        self._marshal(0)

    @ZcosmicWorkspaceManagerV1.request()
    def stop(self) -> None:
        """Stop sending events

        Indicates the client no longer wishes to receive events for new
        workspace groups. However the compositor may emit further workspace
        events, until the finished event is emitted.

        The client must not send any more requests after this one.
        """
        self._marshal(1)


class ZcosmicWorkspaceManagerV1Resource(Resource):
    interface = ZcosmicWorkspaceManagerV1

    @ZcosmicWorkspaceManagerV1.event(
        Argument(ArgumentType.NewId, interface=ZcosmicWorkspaceGroupHandleV1),
    )
    def workspace_group(self, workspace_group: ZcosmicWorkspaceGroupHandleV1) -> None:
        """A workspace group has been created

        This event is emitted whenever a new workspace group has been created.

        All initial details of the workspace group (workspaces, outputs) will
        be sent immediately after this event via the corresponding events in
        :class:`~pywayland.protocol.cosmic_workspace_unstable_v1.ZcosmicWorkspaceGroupHandleV1`.

        :param workspace_group:
        :type workspace_group:
            :class:`~pywayland.protocol.cosmic_workspace_unstable_v1.ZcosmicWorkspaceGroupHandleV1`
        """
        self._post_event(0, workspace_group)

    @ZcosmicWorkspaceManagerV1.event()
    def done(self) -> None:
        """All information about the workspace groups has been sent

        This event is sent after all changes in all workspace groups have been
        sent.

        This allows changes to one or more
        :class:`~pywayland.protocol.cosmic_workspace_unstable_v1.ZcosmicWorkspaceGroupHandleV1`
        properties and
        :class:`~pywayland.protocol.cosmic_workspace_unstable_v1.ZcosmicWorkspaceHandleV1`
        properties to be seen as atomic, even if they happen via multiple
        events. In particular, an output moving from one workspace group to
        another sends an output_enter event and an output_leave event to the
        two
        :class:`~pywayland.protocol.cosmic_workspace_unstable_v1.ZcosmicWorkspaceGroupHandleV1`
        objects in question. The compositor sends the done event only after
        updating the output information in both workspace groups.
        """
        self._post_event(1)

    @ZcosmicWorkspaceManagerV1.event()
    def finished(self) -> None:
        """The compositor has finished with the workspace_manager

        This event indicates that the compositor is done sending events to the
        :class:`ZcosmicWorkspaceManagerV1`. The server will destroy the object
        immediately after sending this request, so it will become invalid and
        the client should free any resources associated with it.
        """
        self._post_event(2)


class ZcosmicWorkspaceManagerV1Global(Global):
    interface = ZcosmicWorkspaceManagerV1


ZcosmicWorkspaceManagerV1._gen_c()
ZcosmicWorkspaceManagerV1.proxy_class = ZcosmicWorkspaceManagerV1Proxy
ZcosmicWorkspaceManagerV1.resource_class = ZcosmicWorkspaceManagerV1Resource
ZcosmicWorkspaceManagerV1.global_class = ZcosmicWorkspaceManagerV1Global
