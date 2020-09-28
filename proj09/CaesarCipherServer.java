import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.lang.Character;
import java.time.format.DateTimeFormatter;  
import java.time.LocalDateTime;  
import java.lang.Thread;  

public class CaesarCipherServer extends Thread
{
    private ServerSocket serverSocket;
    private int port;
    private boolean running = false;

    public CaesarCipherServer( int port )
    {
        this.port = port;
    }

    public void startServer()
    {
        try
        {
            serverSocket = new ServerSocket( port );
            this.start();
        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
    }

    public void stopServer()
    {
        running = false;
        this.interrupt();
    }

    @Override
    public void run()
    {
        running = true;
        while( running )
        {
            try
            {
                System.out.println( "Listening for a connection" );

                // Call accept() to receive the next connection
                Socket socket = serverSocket.accept();

                // Pass the socket to the RequestHandler thread for processing
                RequestHandler requestHandler = new RequestHandler( socket );
                requestHandler.start();
            }
            catch (IOException e)
            {
                e.printStackTrace();
            }
        }
    }

    public static void main( String[] args )
    {
        if( args.length == 0 )
        {
            System.out.println( "Usage: CaesarCipherServer <port>" );
            System.exit( 0 );
        }
        int port = Integer.parseInt( args[ 0 ] );
        System.out.println( "Start server on port: " + port );

        CaesarCipherServer server = new CaesarCipherServer( port );
        server.startServer();

        // Automatically shutdown in 1 minute
        try
        {
            Thread.sleep( 60000 );
        }
        catch( Exception e )
        {
            e.printStackTrace();
        }

        server.stopServer();
    }
}

class RequestHandler extends Thread
{
    private Socket socket;

    RequestHandler( Socket socket )
    {
        this.socket = socket;
    }

    @Override
    public void run()
    {
        try
        {
            DateTimeFormatter dtf = DateTimeFormatter.ofPattern("MM/dd/yyyy HH:mm:ss");  
            LocalDateTime now = LocalDateTime.now();  
            System.out.println( dtf.format(now) + " Received a connection from " + socket.getRemoteSocketAddress().toString());

            // Get input and output streams
            BufferedReader in = new BufferedReader( new InputStreamReader( socket.getInputStream() ) );
            PrintWriter out = new PrintWriter( socket.getOutputStream() );

            // Echo lines back to the client until the client closes the connection or we receive an empty line
            String line = in.readLine();
            try{
                int rotation = Integer.parseInt(line);
                String result = "";
                int originalPos = 0;
                int newPos = 0;
                char newChar = 'a';

                if(rotation > 0 && rotation < 26) {
                    out.println(rotation);
                    out.flush();
                    line = in.readLine();
                    while( line != null && line.length() > 0 )
                    {
                        result = "";
                        for(int i = 0; i < line.length(); ++i ) {
                            if(line.charAt(i) == ' '){
                                result += ' ';
                            }
                            else if(Character.isUpperCase(line.charAt(i))){
                                originalPos = line.charAt(i) - 'A';
                                newPos = (originalPos + rotation) % 26;
                                newChar = (char) ('A' + newPos);
                                result += newChar;
                            }
                            else {
                                originalPos = line.charAt(i) - 'a';
                                newPos = (originalPos + rotation) % 26;
                                newChar = (char) ('a' + newPos);
                                result += newChar;
                            }
                        }
                        out.println(result);
                        out.flush();
                        line = in.readLine();
                    }
                }
                else {
                    out.println("Invalid rotation number");
                }

            // Close our connection
                in.close();
                out.close();
                socket.close();

                System.out.println( "Connection closed" );
            }
            catch(NumberFormatException e)
            {
                in.close();
                out.close();
                socket.close();
                System.out.println( "Connection closed" );
                System.out.flush();
                System.out.println("Input given by client was not a number");
            }
        }
        catch( Exception e )
        {
            e.printStackTrace();
        }
    }
}