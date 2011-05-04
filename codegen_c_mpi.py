#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# C + MPI
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2009, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2009).  Los Alamos National Security, LLC.  This software
# was produced under U.S. Government contract DE-AC52-06NA25396
# for Los Alamos National Laboratory (LANL), which is operated by
# Los Alamos National Security, LLC (LANS) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
# MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
# FOR THE USE OF THIS SOFTWARE. If software is modified to produce
# derivative works, such modified software should be clearly marked,
# so as not to confuse it with the version available from LANL.
# 
# Additionally, redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the
# following conditions are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer
#     in the documentation and/or other materials provided with the
#     distribution.
# 
#   * Neither the name of Los Alamos National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################

import string
import codegen_c_generic
from ncptl_config import ncptl_config

class NCPTL_CodeGen(codegen_c_generic.NCPTL_CodeGen):

    def __init__(self, options=None):
        "Initialize the C + MPI code generation module."
        codegen_c_generic.NCPTL_CodeGen.__init__(self, options)
        self.backend_name = "c_mpi"
        self.backend_desc = "C + MPI"

        # Determine the set of build parameters to use.
        self.set_param("CC", "replace",
                       self.get_param("MPICC", self.get_param("CC", "cc")))
        self.set_param("CPPFLAGS", "append",
                       self.get_param("MPICPPFLAGS", ""))
        self.set_param("CFLAGS", "replace",
                       self.get_param("MPICFLAGS",
                                      self.get_param("CFLAGS", "")))
        self.set_param("LDFLAGS", "prepend",
                       self.get_param("MPILDFLAGS", ""))
        self.set_param("LIBS", "prepend",
                       self.get_param("MPILIBS", ""))

        # Process any command-line options targeting the backend itself.
        self.send_function = "MPI_Send"
        self.isend_function = "MPI_Isend"
        self.reduce_operation = "MPI_SUM"
        for arg in range(0, len(options)):
            if options[arg] == "--ssend":
                # Use MPI_Send() unless the --ssend option is given,
                # in which case we use MPI_Ssend().
                self.send_function = "MPI_Ssend"
                self.isend_function = "MPI_Issend"
            elif options[arg][:9] == "--reduce=":
                # Reduce using MPI_SUM unless an alternative is named.
                self.reduce_operation = options[arg][9:]
            elif options[arg] == "--help":
                # Output a help message.
                self.cmdline_options.extend([
                    ("--ssend",
                     """Use MPI_Ssend() for point-to-point
                                  communication instead of MPI_Send()"""),
                    ("--reduce=<string>",
                     """Specify an MPI reduce operator to use for
                                  MPI_Reduce() and MPI_Allreduce()
                                  [default: MPI_SUM]""")])
                self.show_help()
                raise SystemExit, 0


    # ----------- #
    # Header code #
    # ----------- #

    def code_specify_include_files_POST(self, localvars):
        "Specify extra header files needed by the c_mpi backend."
        return [
            "#include <mpi.h>",
            "#include <stdarg.h>"]

    def code_define_macros_POST(self, localvars):
        "Define some macros to simplify the generated C code."
        newmacros = []
        newmacros.extend([
            "/* Estimate the number of unique communicators that this program will need.",
            " * (The tradeoff is one of initialization time versus memory consumption.) */",
            "#define ESTIMATED_COMMUNICATORS 128",
            "",
            "/* Specify an operation to use for all reduction operations. */",
            "#define REDUCE_OPERATION %s" % self.reduce_operation,
            '#define REDUCE_OPERATION_NAME "%s"' % self.reduce_operation,
            ""])
        return newmacros

    def code_declare_globals_EXTRA(self, localvars):
        "Declare additional C global variables needed by the c_mpi backend."
        newvars = []
        self.code_declare_var(name="mpi_is_running", rhs="0",
                              comment="1=MPI has been initialized",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="recvreqQ",
                              comment="List of MPI receive requests",
                              stack=newvars)
        self.code_declare_var(type="MPI_Request *", name="recvrequests",
                              comment="List version of recvreqQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="recvstatQ",
                              comment="List of MPI receive statuses",
                              stack=newvars)
        self.code_declare_var("MPI_Status *", name="recvstatuses",
                              comment="List version of recvstatQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="sendreqQ",
                              comment="List of MPI send requests",
                              stack=newvars)
        self.code_declare_var(type="MPI_Request *", name="sendrequests",
                              comment="List version of sendreqQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="sendstatQ",
                              comment="List of MPI send statuses",
                              stack=newvars)
        self.code_declare_var(type="MPI_Status *", name="sendstatuses",
                              comment="List version of sendstatQ",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_SET *", name="communicators",
                              comment="Map from an array of processor flags to an MPI communicator",
                              stack=newvars)
        self.code_declare_var(type="MPI_Errhandler", name="mpi_error_handler",
                              comment="Handle to handle_MPI_error()",
                              stack=newvars)

        # Make all declarations static.
        static_newvars = []
        for var in newvars:
            static_newvars.append("static " + var)
        return static_newvars


    # -------------- #
    # Initialization #
    # -------------- #

    def code_def_init_decls_POST(self, localvars):
        "Declare variables needed by code_define_functions_INIT_COMM_1."
        newvars = []
        self.code_declare_var(type="int", name="num_tasks",
                              comment="int version of var_num_tasks needed by MPI_Comm_size()",
                              stack=newvars)
        self.code_declare_var(type="char *", name="procflags",
                              comment="Array of 1s representing an all-task MPI communicator",
                              stack=newvars)
        self.code_declare_var(type="MPI_Comm", name="comm_world", rhs="MPI_COMM_WORLD",
                              comment="Copy of MPI_COMM_WORLD that we can take the address of",
                              stack=newvars)
        return newvars

    def code_def_init_init_PRE(self, localvars):
        "Define extra initialization to be performed before ncptl_init()."
        return [
            " /* Initialize MPI. */",
            "(void) MPI_Init(&argc, &argv);",
            "mpi_is_running = 1;"]

    def code_define_functions_INIT_COMM_1(self, localvars):
        "Define extra initialization to be performed after ncptl_init()."
        return [
            "(void) MPI_Errhandler_create ((MPI_Handler_function *)handle_MPI_error, &mpi_error_handler);",
            "(void) MPI_Errhandler_set (MPI_COMM_WORLD, mpi_error_handler);",
            "(void) MPI_Comm_rank(MPI_COMM_WORLD, &physrank);",
            "(void) MPI_Comm_size(MPI_COMM_WORLD, &num_tasks);",
            "var_num_tasks = (ncptl_int) num_tasks;"]

    def code_define_functions_PRE(self, localvars):
        "Define some additional functions we need at run time."
        return [
            "/* Make MPI errors invoke ncptl_fatal(). */",
            "static void handle_MPI_error (MPI_Comm *comm, int *errcode, ...)",
            "{",
            "va_list args;",
            "char errstring[MPI_MAX_ERROR_STRING];",
            "int errstrlen;",
            "",
            "va_start (args, errcode);",
            "if (MPI_Error_string (*errcode, errstring, &errstrlen) == MPI_SUCCESS)",
            'ncptl_fatal ("MPI run-time error: %s", errstring);',
            "else",
            'ncptl_fatal ("MPI aborted with unrecognized error code %d", *errcode);',
            "conc_dummy_var.vp = (void *) comm;   /* Prevent the compiler from complaining that comm is unused. */",
            "va_end (args);",
            "}",
            "",
            "/* Perform the equivalent of MPI_Comm_rank() for an arbitrary process. */",
            "static int rank_in_MPI_communicator (MPI_Comm subcomm, int global_rank)",
            "{",
            "  MPI_Group world_group;   /* Group associated with MPI_COMM_WORLD */",
            "  MPI_Group subgroup;      /* Group associate with subcomm */",
            "  int subrank;             /* global_rank's rank within subcomm */",
            "",
            "  MPI_Comm_group (MPI_COMM_WORLD, &world_group);",
            "  MPI_Comm_group (subcomm, &subgroup);",
            "  MPI_Group_translate_ranks (world_group, 1, &global_rank, subgroup, &subrank);",
            "  return subrank;",
            "}",
            "",
            "/* Given an array of task in/out booleans return an MPI",
            ' * communicator that represents the "in" tasks. */',
            "static MPI_Comm define_MPI_communicator (char *procflags)",
            "{",
            "MPI_Comm *existing_comm;    /* Previously defined MPI communicator */",
            "MPI_Comm new_comm;          /* Newly defined MPI communicator */",
            "",
            "existing_comm = (MPI_Comm *) ncptl_set_find (communicators, (void *)procflags);",
            "if (existing_comm)",
            "return *existing_comm;",
            "(void) MPI_Comm_split (MPI_COMM_WORLD, (int)procflags[physrank], physrank, &new_comm);",
            "(void) MPI_Errhandler_set (new_comm, mpi_error_handler);",
            "ncptl_set_insert (communicators, (void *)procflags, (void *)&new_comm);",
            "return define_MPI_communicator (procflags);",
            "}"]

    def code_def_init_cmd_line_PRE_PARSE(self, localvars):
        "Prevent MPI_Abort() from being called by --help."
        return ["mpi_is_running = 0;   /* Don't invoke MPI_Abort() after --help. */"]

    def code_def_init_cmd_line_POST_PARSE(self, localvars):
        "Re-enable MPI_Abort()."
        return ["mpi_is_running = 1;"]

    def code_def_init_misc_PRE_LOG_OPEN(self, localvars):
        "Add an extra line to the log file."
        extraloglines = []
        if self.program_uses_log_file:
            extraloglines.extend([
                'ncptl_log_add_comment ("MPI send routines", "%s() and %s()");' %
                (self.send_function, self.isend_function),
                'ncptl_log_add_comment ("MPI reduction operation", REDUCE_OPERATION_NAME);'])
        return extraloglines

    def code_def_init_misc_EXTRA(self, localvars):
        "Initialize everything else that needs to be initialized."
        return [
            "sendreqQ = ncptl_queue_init (sizeof (MPI_Request));",
            "sendstatQ = ncptl_queue_init (sizeof (MPI_Status));",
            "recvreqQ = ncptl_queue_init (sizeof (MPI_Request));",
            "recvstatQ = ncptl_queue_init (sizeof (MPI_Status));",
            "communicators = ncptl_set_init (ESTIMATED_COMMUNICATORS, var_num_tasks*sizeof(char), sizeof(MPI_Comm));"
            "procflags = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);",
            "for (i=0; i<var_num_tasks; i++)",
            "procflags[i] = 1;",
            "ncptl_set_insert (communicators, (void *)procflags, (void *)&comm_world);",
            "ncptl_free (procflags);"]

    def code_define_main_POST_INIT(self, localvars):
        "Finalize the various asynchronous-data queues into lists."
        return [
            "sendrequests = (MPI_Request *) ncptl_queue_contents (sendreqQ, 0);",
            "sendstatuses = (MPI_Status *) ncptl_queue_contents (sendstatQ, 0);",
            "recvrequests = (MPI_Request *) ncptl_queue_contents (recvreqQ, 0);",
            "recvstatuses = (MPI_Status *) ncptl_queue_contents (recvstatQ, 0);"]

    def code_def_init_reseed_BCAST(self, localvars):
        "Broadcast a random-number seed to all tasks."
        bcastcode = []
        self.push("{", bcastcode)
        self.code_declare_var(type="int", name="rndseed_int",
                              rhs="(int) random_seed",
                              comment="Version of random_seed with int type",
                              stack=bcastcode)
        self.pushmany([
            "(void) MPI_Bcast ((void *)&rndseed_int, 1, MPI_INT, 0, MPI_COMM_WORLD);",
            "random_seed = (ncptl_int) rndseed_int;",
            "}"],
                      stack=bcastcode)
        return bcastcode

    def code_def_init_uuid_BCAST(self, locals):
        "Broadcast logfile_uuid to all tasks."
        return ["(void) MPI_Bcast ((void *)logfile_uuid, 37, MPI_CHAR, 0, MPI_COMM_WORLD);"]

    def code_def_mark_used_POST(self, locals):
        "Indicate that rank_in_MPI_communicator() is not an unused function."
        return ["rank_in_MPI_communicator (MPI_COMM_WORLD, 0);"]


    # ------------ #
    # Finalization #
    # ------------ #

    def code_def_finalize_DECL(self, localvars):
        "Store the return value of MPI_Finalize()."
        newvars = []
        self.code_declare_var(type="int", name="mpiresult",
                              comment="Return code from MPI_Finalize()",
                              stack=newvars)
        return newvars

    def code_def_finalize_POST(self, localvars):
        "Finish up cleanly."
        return [
            "mpiresult = MPI_Finalize();",
            "mpi_is_running = 0;",
            "exitcode = mpiresult!=MPI_SUCCESS;"]

    def code_def_exit_handler_BODY(self, localvars):
        """
             Terminate all processes in the program if we exited
             without calling conc_finalize().
        """
        return [
            "if (mpi_is_running)",
            "MPI_Abort (MPI_COMM_WORLD, 1);"]


    # ---------------------------- #
    # Point-to-point communication #
    # ---------------------------- #

    def code_declare_datatypes_SEND_STATE(self, localvars):
        "Declare fields in the CONC_SEND_EVENT structure for send events."
        newfields = []
        self.code_declare_var(type="MPI_Request *", name="handle",
                              comment="MPI handle representing an asynchronous send",
                              stack=newfields)
        return newfields

    def code_declare_datatypes_RECV_STATE(self, localvars):
        "Declare fields in the CONC_RECV_EVENT structure for receive events."
        newfields = []
        self.code_declare_var(type="MPI_Request *", name="handle",
                              comment="MPI handle representing an asynchronous receive",
                              stack=newfields)
        return newfields

    def code_def_init_msg_mem_PRE(self, localvars):
        "Flatten sendreqQ and recvreqQ into lists for use by code_def_init_msg_mem_EACH_TAG."
        return [
            "sendrequests = (MPI_Request *) ncptl_queue_contents (sendreqQ, 0);",
            "recvrequests = (MPI_Request *) ncptl_queue_contents (recvreqQ, 0);"]

    def code_def_init_msg_mem_EACH_TAG(self, localvars):
        "Store pointers into sendrequests and recvrequests."
        handlecode = []
        tag = localvars["tag"]
        struct = localvars["struct"]
        if tag == "EV_ASEND":
            self.push("%s.handle = &sendrequests[%s.pendingsends-1];" %
                      (struct, struct),
                      handlecode)
        elif tag == "EV_ARECV":
            self.push("%s.handle = &recvrequests[%s.pendingrecvs-1];" %
                      (struct, struct),
                      handlecode)
        elif tag == "EV_REDUCE":
            self.pushmany([
                "if (!%s.altbuffer && %s.receiving)" % (struct, struct),
                "%s.altbuffer = ncptl_malloc_message (%s.numitems * %s.itemsize," % (struct, struct, struct),
                "%s.alignment," % struct,
                "%s.buffernum+1,   /* Note that reduces use _two_ buffers. */" % struct,
                "%s.misaligned);" % struct],
                          stack=handlecode)
        return handlecode

    def n_send_stmt_BODY(self, localvars):
        "Allocate memory for additional pending sends."
        if "asynchronously" in localvars["attributes"]:
            return [
                "(void *) ncptl_queue_allocate (sendreqQ);",
                "(void *) ncptl_queue_allocate (sendstatQ);"]
        else:
            return []

    def n_recv_stmt_BODY(self, localvars):
        "Allocate memory for additional pending receives."
        if "asynchronously" in localvars["attributes"]:
            return [
                "(void *) ncptl_queue_allocate (recvreqQ);",
                "(void *) ncptl_queue_allocate (recvstatQ);"]
        else:
            return []

    def code_def_procev_DECL(self, localvars):
        "Declare a status variable for MPI_Recv()."
        newdecls = []
        if self.events_used.has_key("EV_RECV"):
            self.code_declare_var(type="MPI_Status", name="status",
                                  comment="Not needed but required by MPI_Recv()",
                                  stack=newdecls)
        return newdecls

    def code_def_procev_send_BODY(self, localvars):
        "Send a message down a given channel (blocking)."
        return [
            "(void) %s (thisev->s.send.buffer, (int)thisev->s.send.size, MPI_BYTE," % self.send_function,
            "(int)thisev->s.send.dest, 0, MPI_COMM_WORLD);"]

    def code_def_procev_recv_BODY(self, localvars):
        "Receive a message from a given channel (blocking)."
        return [
            "(void) MPI_Recv (thisev->s.recv.buffer, (int)thisev->s.recv.size, MPI_BYTE,",
            "(int)thisev->s.recv.source, 0, MPI_COMM_WORLD, &status);"]

    def code_def_procev_asend_BODY(self, localvars):
        "Perform an asynchronous send."
        return [
            "(void) %s (thisev->s.send.buffer, (int)thisev->s.send.size, MPI_BYTE," % self.isend_function,
            "(int)thisev->s.send.dest, 0, MPI_COMM_WORLD, thisev->s.send.handle);"]

    def code_def_procev_arecv_BODY(self, localvars):
        "Perform an asynchronous receive."
        return [
            "(void) MPI_Irecv (thisev->s.recv.buffer, (int)thisev->s.recv.size, MPI_BYTE,",
            "(int)thisev->s.recv.source, 0, MPI_COMM_WORLD, thisev->s.recv.handle);"]

    def code_def_procev_wait_BODY_SENDS(self, localvars):
        "Retry all of the sends that blocked."
        return [
            "(void) MPI_Waitall ((int)thisev->s.wait.numsends, sendrequests, sendstatuses);"]

    def code_def_procev_wait_BODY_RECVS(self, localvars):
        "Retry all of the receives that blocked."
        return [
            "(void) MPI_Waitall ((int)thisev->s.wait.numrecvs, recvrequests, recvstatuses);"]


    # ------------------------ #
    # Collective communication #
    # ------------------------ #

    def code_declare_datatypes_SYNC_STATE(self, localvars):
        "Declare fields in the CONC_SYNC_EVENT structure for synchronization events."
        newfields = []
        self.code_declare_var(type="MPI_Comm", name="communicator",
                              comment="Set of tasks to synchronize",
                              stack=newfields)
        return newfields

    def code_declare_communicator(self, source_task, stack):
        """
             Return an MPI communicator representing a set of tasks.
             Note that the source_task argument is allowed to be of
             target_tasks type.
        """
        base_comm = "MPI_COMM_WORLD"
        if source_task[0]=="task_all" or source_task[0]=="all_others":
            return base_comm
        elif source_task[0] in ["task_restricted", "task_expr"]:
            if source_task[0] == "task_expr":
                expression_name = "task %s" % source_task[1]
            else:
                expression_name = "tasks %s such that %s" % source_task[1:3]
            self.pushmany([
                " /* Define a communicator representing %s. */" % expression_name],
                          stack)
            self.code_declare_var(type="char *", name="procflags", rhs="NULL",
                                  comment="Flags indicating whether each task is in or out",
                                  stack=stack)
            self.code_declare_var(type="MPI_Comm", name="subcom",
                                  comment="MPI subcommunicator to use",
                                  stack=stack)
            if source_task[0] == "task_expr":
                loopvar = self.code_declare_var(suffix="loop", stack=stack)
                expression = "(%s == (%s))" % (loopvar, source_task[1])
            else:
                loopvar = source_task[1]
                expression = source_task[2]
                self.code_declare_var(name=loopvar, stack=stack)
            self.pushmany([
                "",
                " /* Determine the set of participating tasks. */",
                "procflags = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);",
                "for (%s=0; %s<var_num_tasks; %s++)" % (loopvar, loopvar, loopvar),
                "procflags[ncptl_virtual_to_physical(procmap, %s)] = %s;" % (loopvar, expression),
                "",
                "subcom = define_MPI_communicator (procflags);",
                "ncptl_free (procflags);"],
                          stack)
            return "subcom"
        else:
            self.errmsg.error_internal('unable to declare an MPI communicator for source task "%s"' % source_task[0])

    def n_sync_stmt_DECL(self, localvars):
        "Declare a communicator representing the tasks to synchronize."
        synccode = []
        self.communicator = self.code_declare_communicator(localvars["source_task"],
                                                           synccode)
        return synccode

    def n_sync_stmt_INIT(self, localvars):
        "Return the communicator selected by n_sync_stmt_DECL."
        return ["thisev->s.sync.communicator = %s;" % self.communicator]

    def code_def_procev_sync_BODY(self, localvars):
        "Synchronize a set of tasks."
        return ["(void) MPI_Barrier (thisev->s.sync.communicator);"]

    def n_for_count_SYNC_ALL(self, localvars):
        "Prepare to synchronize all of the tasks in the job."
        return ["thisev_sync->s.sync.communicator = MPI_COMM_WORLD;"]

    def code_def_procev_etime_REDUCE_MIN(self, localvars):
        "Find the global minimum of the elapsedtime variable."
        return [
            "(void) MPI_Allreduce (&elapsedtime, &minelapsedtime,",
            "1, MPI_LONG_LONG_INT, MPI_MIN, MPI_COMM_WORLD);"]

    def code_declare_datatypes_MCAST_STATE(self, localvars):
        "Declare fields in the CONC_MCAST_EVENT structure for multicast events."
        newfields = []
        self.code_declare_var(type="MPI_Comm", name="communicator",
                              comment="Set of tasks to multicast to/from",
                              stack=newfields)
        self.code_declare_var(type="int", name="root",
                              comment="source's rank within communicator",
                              stack=newfields)
        return newfields

    def n_mcast_stmt_DECL(self, localvars):
        "Declare a communicator representing the tasks to multicast to/from."
        mcastcode = []
        self.communicator = self.code_declare_communicator(localvars["target_or_source"],
                                                           mcastcode)
        return mcastcode

    def n_mcast_stmt_INIT(self, localvars):
        "Return the communicator selected by n_mcast_stmt_DECL."
        struct = localvars["struct"]
        return [
            "%s.communicator = %s;" % (struct, self.communicator),
            "%s.root = rank_in_MPI_communicator (%s.communicator, %s.source);" %
            (struct, struct, struct)]

    def code_def_procev_mcast_BODY(self, localvars):
        "Multicast a message to a set of tasks."
        return [
            "(void) MPI_Bcast (thisev->s.mcast.buffer, thisev->s.mcast.size, MPI_BYTE,",
            "thisev->s.mcast.root, thisev->s.mcast.communicator);"]

    def code_declare_datatypes_REDUCE_STATE(self, localvars):
        "Declare fields in the CONC_REDUCE_EVENT structure for reduction events."
        newfields = []
        self.code_declare_var(type="void *", name="altbuffer",
                              comment="Pointer to additional message memory",
                              stack=newfields)
        self.code_declare_var(type="MPI_Comm", name="sendcomm",
                              comment="Set of tasks to reduce from",
                              stack=newfields)
        self.code_declare_var(type="MPI_Comm", name="recvcomm",
                              comment="Set of tasks to reduce to",
                              stack=newfields)
        self.code_declare_var(type="MPI_Datatype", name="datatype",
                              comment="MPI datatype to reduce",
                              stack=newfields)
        self.code_declare_var(type="int", name="reducetype",
                              comment="0=reduce; 1=allreduce; 2=reduce+bcast",
                              stack=newfields)
        self.code_declare_var(name="reduceroot",
                              comment="Root task of the reduction if reducetype is 0 or 2",
                              stack=newfields)
        self.code_declare_var(name="bcastroot",
                              comment="Root task of the multicast if reducetype is 2",
                              stack=newfields)
        return newfields

    def n_reduce_stmt_DECL(self, localvars):
        "Declare variables needed to characterize the reduction."
        reducecode = []
        allreduce = localvars["allreduce"]
        if not allreduce:
            self.code_declare_var(type="int", name="allreduce",
                                  comment="1=senders are the same as receivers",
                                  stack=reducecode)
            self.code_declare_var(type="int", name="disjoint",
                                  comment="1=no sender is also a receiver",
                                  stack=reducecode)
            self.code_declare_var(name="first_shared",
                                  rhs="-1%s" % self.ncptl_int_suffix,
                                  comment="Task ID of the first task that's both a sender and a receiver",
                                  stack=reducecode)
        self.code_declare_var(type="MPI_Comm", name="sendcomm",
                              comment="Set of tasks to reduce from",
                              stack=reducecode)
        self.code_declare_var(type="MPI_Comm", name="recvcomm",
                              comment="Set of tasks to reduce to",
                              stack=reducecode)
        return reducecode

    def n_reduce_stmt_HAVE_PEERS(self, localvars):
        "Determine the type of reduction operation we're about to perform"
        reducecode = []
        allreduce = localvars["allreduce"]

        # Determine at run time if we have an all-reduce situation.
        if not allreduce:
            self.pushmany([
                " /* Determine if the set of senders matches",
                "  * exactly the set of receivers. */",
                "allreduce = 1;",
                "for (i=0; i<var_num_tasks; i++)",
                "if (reduce_receivers[i] != reduce_senders[i]) {",
                "allreduce = 0;",
                "break;",
                "}",
                "",
                " /* Store the task ID of the first task that's both a sender and a receiver. */",
                "if (!allreduce)",
                "for (i=0; i<var_num_tasks; i++)",
                "if (reduce_senders[i] && reduce_receivers[i]) {",
                "first_shared = i;",
                "break;",
                "}",
                "",
                " /* Bridge a disjoint reduce/broadcast by ensuring",
                "  * that the first sender is also a receiver. */",
                "disjoint = first_shared == -1%s;" % self.ncptl_int_suffix,
                "if (disjoint)",
                "for (i=0; i<var_num_tasks; i++)",
                "if (reduce_senders[i]) {",
                "reduce_receivers[i] = 1;",
                "first_shared = i;",
                "break;"
                "}"],
                          stack=reducecode)

        # Create a send communicator by faking a source_task tuple.
        self.pushmany([
            "",
            " /* Store a communicator that represents the physical ranks of reduce_senders[]. */",
            "{"],
                      stack=reducecode)
        loopvar = self.newvar(suffix="loop")
        sender_tasks = ("task_restricted", loopvar, "reduce_senders[%s]" % loopvar)
        sendcomm = self.code_declare_communicator(sender_tasks, reducecode)
        self.push("sendcomm = %s;" % sendcomm, reducecode)
        if allreduce:
            self.push("recvcomm = %s;" % sendcomm, reducecode)
        self.push("}", reducecode)

        # Create a receive communicator by faking a source_task tuple.
        if not allreduce:
            self.pushmany([
                "",
                " /* Store a communicator that represents the physical ranks of reduce_receivers[]. */",
                "{"],
                          stack=reducecode)
            loopvar = self.newvar(suffix="loop")
            receiver_tasks = ("task_restricted", loopvar, "reduce_receivers[%s]" % loopvar)
            recvcomm = self.code_declare_communicator(receiver_tasks, reducecode)
            self.push("recvcomm = %s;" % recvcomm, reducecode)
            self.push("}", reducecode)
        return reducecode

    def n_reduce_stmt_INIT(self, localvars):
        "Define communicators and store both the communicators and the reduction type."
        initcode = []
        struct = localvars["struct"]
        allreduce = localvars["allreduce"]

        # Determine whether to use MPI_Reduce(), MPI_Allreduce(), or
        # MPI_Reduce()+MPI_Bcast().
        if allreduce:
            # We know at compile time that we have an allreduce.
            self.push("%s.reducetype = 1;" % struct, initcode)
        else:
            # We have to check at run time for the type of reduction.
            self.pushmany([
                "",
                " /* Store the type of reduction we intend to perform. */",
                "if (numreceivers == 1 && !disjoint)",
                "%s.reducetype = 0;" % struct,
                "else",
                "if (allreduce)",
                "%s.reducetype = 1;" % struct,
                "else",
                "%s.reducetype = 2;" % struct,
                "",
                " /* Fill in the remainder of the reduce structure. */",
                "%s.reduceroot = rank_in_MPI_communicator (sendcomm, ncptl_virtual_to_physical(procmap, first_shared));" % struct,
                "%s.bcastroot = rank_in_MPI_communicator (recvcomm, ncptl_virtual_to_physical(procmap, first_shared));" % struct],
                          stack=initcode)
        return initcode

    def n_reduce_stmt_INIT2(self, localvars):
        "Assign a value to the altbuffer member of the reduce structure."
        initcode = []
        struct = localvars["struct"]

        # Handle the alternate buffer field differently based on whether the
        # message buffer is supposed to be unique.
        self.push(" /* Perform some c_mpi-specific structure initialization. */", initcode)
        if string.upper(localvars["uniqueness"]) == "UNIQUE":
            alignment = localvars["alignment"]
            self.push("if (%s.receiving)" % struct, initcode)
            if localvars["misaligned"]:
                self.push("%s.altbuffer = ncptl_malloc_misaligned (message_size, %s);" %
                          (struct, alignment),
                          initcode)
            else:
                self.push("%s.altbuffer = ncptl_malloc (message_size, %s);" %
                          (struct, alignment),
                          initcode)
            self.push("else", initcode)
            self.push("%s.altbuffer = NULL;" % struct, initcode)
        else:
            # We don't have to invoke ncptl_malloc_message here
            # because the parameters are the same as for the BUFFER
            # structure member.
            self.push("%s.altbuffer = NULL;" % struct, initcode)
        self.pushmany([
            "switch (%s.itemsize) {" % struct,
            "case 4%s:" % self.ncptl_int_suffix,
            "%s.datatype = MPI_INT;" % struct,
            "break;",
            "",
            "case 8%s:" % self.ncptl_int_suffix,
            "%s.datatype = MPI_DOUBLE;" % struct,
            "break;",
            "",
            "default:",
            'ncptl_fatal ("Internal error -- unable to reduce data of size %%" NICS " byte(s)", %s.itemsize);' % struct,
            "break;",
            "}",
            "%s.sendcomm = sendcomm;" % struct,
            "%s.recvcomm = recvcomm;" % struct,
            "(void) ncptl_malloc_message (message_size, %s.alignment, %s.buffernum+1, %s.misaligned);   /* altbuffer uses buffernum+1. */" %
            (struct, struct, struct)],
                      stack=initcode)
        return initcode

    def code_def_procev_reduce_BODY(self, localvars):
        "Reduce one or more values and distribute the result."
        struct = "thisev->s.reduce"
        reducecode = []
        self.pushmany([
            "switch (%s.reducetype) {" % struct,
            "case 0:",
            " /* Reduce to a single task. */",
            "(void) MPI_Reduce (%s.buffer, %s.altbuffer, %s.numitems," %
            (struct, struct, struct),
            "%s.datatype, REDUCE_OPERATION, %s.reduceroot, %s.sendcomm);" %
            (struct, struct, struct),
            "break;",
            "",
            "case 1:",
            " /* Reduce from a set of tasks to the same set of tasks. */",
            "(void) MPI_Allreduce (%s.buffer, %s.altbuffer, %s.numitems," %
            (struct, struct, struct),
            "%s.datatype, REDUCE_OPERATION, %s.sendcomm);" % (struct, struct),
            "break;",
            "",
            "case 2:",
            " /* Reduce from one set of tasks to a different set. */",
            "if (%s.sending)" % struct,
            "(void) MPI_Reduce (%s.buffer, %s.altbuffer, %s.numitems," %
            (struct, struct, struct),
            "%s.datatype, REDUCE_OPERATION, %s.reduceroot, %s.sendcomm);" %
            (struct, struct, struct),
            "if (%s.receiving)" % struct,
            "(void) MPI_Bcast (%s.altbuffer, %s.numitems," % (struct, struct),
            "%s.datatype, %s.bcastroot, %s.recvcomm);" % ((struct,)*3),
            "break;",
            "",
            "default:",
            'ncptl_fatal ("Internal error -- unknown reduction type");',
            "}"],
                      stack=reducecode)
        if self.program_uses_touching:
            localvars["msgbuffer"] = "%s.altbuffer" % struct
        return reducecode