# IFSTool - Interactive FileSystem Tool

IFSTool is a tool that allows to perform bulk filesystem operations on large number of files in the directory tree using a text editor,
in a similar manner to interactive rebase feature of Git.

## Origin and purpose

Initially called "batch renamer", its goal was to facilitate organization of thousands of files on the hard disk - renaming them with a proper
convention, moving them to appropriate directories and deleting some of them. Doing it with a regular file explorer is of course possible, but
may and surely will be laborous - for example, removal of excess prefix or suffix in the file name would have to be performed one file at a time.
If the entire list of files could be handled with text operations such as search & replace (ideally with regular expressions' support), the operations
could be done much quicker. The work would be even faster if we use an editor with extensive text processing capabilities, such as Vim, which inspired
the overall design of the tool.

## Working with the tool

### Basic usage - example
1. Run ifstool, passing the names of directories you want to work on as the parameters. If you want to work on current directory, simply
use '.' as the name:
        $ *ifstool .*

2. A text editor (Vim by default) will be executed. A list of files found in indicated directories and all their subdirectories will be visible in the editor.
```
00000001 r   ./photo.jpg
00000002 r   ./lol_xd.png
00000003 r   ./some subdirectory/myfile2.txt
00000004 r   ./some subdirectory/myfile3.txt
00000005 r   ./some subdirectory/mycv.doc
00000006 r   ./another subdirectory/myfile1.txt
```

3. Modify the file names in the editor. Want to rename all "my-things" to "My Thing"? Just change the appropriate lines:
```
00000003 r   ./some subdirectory/My File 2.txt
00000004 r   ./some subdirectory/My File 3.txt
00000005 r   ./some subdirectory/My CV.doc
00000006 r   ./another subdirectory/My File 1.txt
```
_Note: Vim commands "Ctrl+V", "Shift+I", "U" will do the job; you can work on multiple lines._

4. If you want to delete any of the files, change the 'r' letter right next to the numeric identifier to 'd':
```
00000002 d   ./lol_xd.png
```

5. When you are done, save the changes and exit the editor. You will be asked for confirmation before each operation is taken:
```
Delete "./lol_xd.png"? [y/N]: y
Rename "myfile2.txt" to "My File 2.txt" in "./some subdirectory"? [y/N]: y
Rename "myfile3.txt" to "My File 3.txt" in "./some subdirectory"? [y/N]: y
Rename "mycv.doc" to "My CV.doc" in "./some subdirectory"? [y/N]: y
Rename "myfile1.txt" to "My File 1.txt" in "./another subdirectory"? [y/N]: y
```

Note that photo.jpg was not affected, since we did not change anything. If you do not want to confirm all the operations, simply add "-y" option to the ifstool invocation.

You can shuffle the lines in the editor if you wish, for example to modify multiple filenames with a single operation in block visual mode. Just pay attention not to alter the
numeric identifier at the beginning of each line, since ifstool uses these identifiers to identify which file was rephrased to what. You can also delete a line with the
file - in such case the file will be left untouched.

