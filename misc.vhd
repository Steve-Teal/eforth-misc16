library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity misc is
	port (
		clock    : in std_logic;
		reset    : in std_logic;
		data_in  : in std_logic_vector(15 downto 0);
		data_out : out std_logic_vector(15 downto 0);
		address  : out std_logic_vector(15 downto 0);
		rd       : out std_logic;
		wr       : out std_logic;
		t1out    : out std_logic);
end entity;

architecture rtl of misc is

type state_type is (T0,T1,T2,T3,T4);
signal state : state_type;

signal address_reg : unsigned(15 downto 0);
signal data_reg    : unsigned(15 downto 0);
signal pc          : unsigned(15 downto 0);
signal accu        : unsigned(15 downto 0);
signal adder_a     : unsigned(15 downto 0);
signal adder_b     : unsigned(15 downto 0);
signal adder_out   : unsigned(16 downto 0);
signal data_mux    : unsigned(15 downto 0);

-- Processor flags

signal sf : std_logic; -- Sign 
signal zf : std_logic; -- Zero
signal cf : std_logic; -- Carry

-- Control

signal dst_pc     : std_logic;
signal data_valid : std_logic;
signal carry_in   : std_logic;
signal subtract   : std_logic;
signal internal   : std_logic;

begin
	
--
-- State machine
--

	process(clock,reset)
	begin
		if rising_edge(clock) then
			if reset = '1' then
				state <= T0;
			else
				case state is
					when T0 =>
						state <= T1;
						t1out <= '1';
					when T1 =>
						state <= T2;
						t1out <= '0';
					when T2 =>
						state <= T3;
					when T3 =>
						state <= T4;
					when T4 =>
						t1out <= '1';
						state <= T1;
				end case;
			end if;
		end if;
	end process;
	
--
-- Address Register
--
	
	process(clock)
	begin
		if rising_edge(clock) then
			case state is
				when T0 =>
					address_reg <= X"0010";
				when T1 =>
					address_reg <= adder_out(15 downto 0);
				when T2|T3 =>
					if data_in = X"0007" then
						address_reg <= accu;
					else
						address_reg <= unsigned(data_in);
					end if;
				when T4 =>
					if dst_pc = '1' then
						address_reg <= data_mux;
					else
						address_reg <= pc;
					end if;
			end case;
		end if;
	end process;
	
--
-- Internal address decode
--

	internal <= '1' when address_reg(15 downto 4) = X"000" else '0';
	
--
-- Program Counter
--

	process(clock)
	begin
		if rising_edge(clock) then
			if state = T2 then
				pc <= adder_out(15 downto 0);
			end if;
		end if;
	end process;
	
--
-- Data Register
--

	process(clock)
	begin
		if rising_edge(clock) then
			if state = T3 then
				case address_reg is
					when X"0000"|X"0001"|X"0002"|X"0003" =>
						data_reg <= adder_out(15 downto 0);
						data_valid <= '1';
					when X"0008" =>
						data_reg <= accu;
						data_valid <= '1';
					when X"0009" =>
						data_reg <= (15 downto 1 => '0') & sf;
						data_valid <= '1';
					when X"000A" =>
						data_reg <= (15 downto 1 => '0') & zf;
						data_valid <= '1';
					when X"000C" =>
						data_reg <= (15 downto 1 => '0') & cf;
						data_valid <= '1';
					when others =>
						data_valid <= '0';
				end case;
			end if;
		end if;
	end process;

--
-- Adder A input source
--

	process(state,pc,data_mux,address_reg,data_in(3 downto 0),subtract)
	begin
		case state is
			when T0 =>
				adder_a <= X"0000";
			when T1|T2 =>
				adder_a <= address_reg;
			when T3 =>
				adder_a <= pc;
			when T4 =>
				if subtract = '1' then 
					adder_a <=  not data_mux;
				else
					adder_a <= data_mux;
				end if;
		end case;
	end process;
			
--
-- Addres B input source
--

	process(state,adder_b,data_in(3 downto 0),accu)
	begin
		case state is
			when T0|T1 =>
				adder_b <= X"0000"; 
			when T2 =>
				adder_b <= X"0000"; 
			when T3 =>
				case address_reg(1 downto 0) is
					when "00" => adder_b <= X"FFFE";
					when "01" => adder_b <= X"0000";
					when "10" => adder_b <= X"0002";
					when "11" => adder_b <= X"0004";
					when others => adder_b <= X"0000";
				end case;
			when T4 =>
					adder_b <= accu;
		end case;
	end process;
	
--
-- Adder
--
 
	adder_out <= ('0' & adder_a) + ('0' & adder_b) + ((15 downto 1 => '0') & carry_in);
	carry_in <= '1' when state = T1 or state = T2 or (state = T4 and subtract = '1') else '0';
	subtract <= '1' when address_reg(3 downto 0) = X"9" else '0';

--
-- Accumulator and carry flag
--

	process(clock)
	begin
		if rising_edge(clock) then
			case state is
				when T0 =>
					accu <= X"0000";
					cf <= '0';
				when T4 =>
					case address_reg is
						when X"0008" =>
							accu <= data_mux;
						when X"0009"|X"000B" =>
							accu <= adder_out(15 downto 0);
							cf <= adder_out(16) xor subtract;
						when X"000C" =>
							accu <= data_mux xor accu;
						when X"000D" =>
							accu <= data_mux or accu;
						when X"000E" =>
							accu <= data_mux and accu;
						when X"000F" =>
							accu <= cf & data_mux(15 downto 1);
							cf <= data_mux(0);
						when others => null;
					end case;
				when others => null;
			end case;
		end if;
	end process;
	
--
-- Zero and Sign flags
--

	zf <= '1' when accu=X"0000" else '0';
	sf <= accu(15);

--
-- Branch logic
--

	with address_reg select dst_pc <= 
		'1' when X"0000",
		sf  when X"0001",
		zf  when X"0002",
		cf  when X"0004",
		'0' when others;
		
--
-- Bus control
--

	process(state,internal)
	begin
		case state is
			when T0 =>
				rd <= '0';
				wr <= '0';
			when T1|T2 =>
				rd <= '1';
				wr <= '0';
			when T3 =>
				rd <= not internal;
				wr <= '0';
			when T4 =>
				rd <= '0';
				wr <= not internal;
		end case;
	end process;
					
--
-- Data and Address bus
--
	
	address <= std_logic_vector(address_reg);
	data_mux <= data_reg when data_valid = '1' else unsigned(data_in);
	data_out <= std_logic_vector(data_mux) when state = T4 and internal = '0' else X"0000";
	
end rtl;

-- End of File
