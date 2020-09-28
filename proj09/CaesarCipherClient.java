import java.net.*;
import java.io.*;

public class CaesarCipherClient {

	public static void main(String []args) {
		System.out.println("Welcome to the Caesar Cipher Client, all messages will be rotated based on a number provided by you.");

		try {
			InetAddress address = InetAddress.getByName(args[0]);
			int port = Integer.parseInt(args[1]);
			Socket stream = new Socket(address, port);
			PrintStream out = new PrintStream(stream.getOutputStream());
			InputStreamReader socketInput = 
				new InputStreamReader(stream.getInputStream());
			BufferedReader in = 
				new BufferedReader(socketInput);
			BufferedReader reader =  
				new BufferedReader(new InputStreamReader(System.in)); 
			String input = "";
			String output = "";

			System.out.print("Enter a rotation integer (1-25): ");
			input = reader.readLine();
			out.println(input);
			output = in.readLine();
			while(!input.equals("quit") && !output.equals(null)) {
				System.out.println(output);
				System.out.print("Enter an input string (type \"quit\" to stop): ");
				input = reader.readLine();
				out.println(input);
				output = in.readLine();
			}

			in.close();
			out.close();
			stream.close();

		}
		catch(UnknownHostException e) {
			System.out.println("Error: Invalid address " + args[0]);
		} 
		catch (IOException e) {
			System.out.println("Error: Invalid port " + args[1]);
		}
		catch(NullPointerException e){
			System.out.println("Error: Invalid input was given. Connection to the server was closed.");
		}
	}
}