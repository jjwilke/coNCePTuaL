/* ----------------------------------------------------------------------
 *
 * coNCePTuaL GUI: exit dialog
 *
 * By Nick Moss <nickm@lanl.gov>
 *
 * This class implements a simple dialog which is shown on exit asking
 * the user whether or not to save changes to file. It is only
 * displayed on exit after determining that there are unsaved changes
 * to the file.
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2015, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2015).  Los Alamos National Security, LLC.  This software
 * was produced under U.S. Government contract DE-AC52-06NA25396
 * for Los Alamos National Laboratory (LANL), which is operated by
 * Los Alamos National Security, LLC (LANS) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
 * MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
 * FOR THE USE OF THIS SOFTWARE. If software is modified to produce
 * derivative works, such modified software should be clearly marked,
 * so as not to confuse it with the version available from LANL.
 * 
 * Additionally, redistribution and use in source and binary forms,
 * with or without modification, are permitted provided that the
 * following conditions are met:
 * 
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 * 
 *   * Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer
 *     in the documentation and/or other materials provided with the
 *     distribution.
 * 
 *   * Neither the name of Los Alamos National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
 * OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
 * BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * 
 *
 * ----------------------------------------------------------------------
 */

package gov.lanl.c3.ncptl;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.event.*;

public class ExitDialog implements ActionListener {

    private JFrame frame;
    private Program program;
    private boolean exit;

    public ExitDialog( Container container, Program program, boolean exit ){
        this.exit = exit;
        this.program = program;
        frame = new JFrame( "Save Changes?" );
        if( container instanceof JFrame )
            frame.setLocationRelativeTo( (JFrame)container );
        else
            if( container instanceof JApplet )
                frame.setLocationRelativeTo( (JApplet)container );

        Container pane = frame.getContentPane();
        pane.setLayout( new FlowLayout( FlowLayout.CENTER ) );

        pane.add( new JLabel( "Save changes before exiting?" ) );

        JButton yesButton = new JButton( "Yes" );
        JButton noButton = new JButton( "No" );
        yesButton.addActionListener( this );
        noButton.addActionListener( this );
        pane.add( yesButton );
        pane.add( noButton );
        frame.pack();
        frame.setVisible( true );
    }

    public void actionPerformed( ActionEvent event ){
        String command = event.getActionCommand();
        if( command.equals( "Yes" ) )
            exit = program.saveOnExit();
        frame.setVisible( false );
        frame.dispose();
        if( exit )
            System.exit( 0 );
    }

}
