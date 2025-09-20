`timescale 1ns/1ns
module Counter_5bit(clk, count_sel, five_init, five_en, cout_down, zero_sum);
    input clk, count_sel, five_init, five_en;
    output cout_down;
    output reg[4:0] zero_sum;
    
    always @(posedge(clk)) begin  
        if (five_init) begin
            zero_sum <= 5'b0; end

        else if(five_en == 1 && count_sel == 0) begin
            zero_sum <= zero_sum + 1;  end
        else if(five_en == 1 && count_sel == 1)  begin
            zero_sum <= zero_sum - 1; end
        
    end  
 
    assign cout_down = ~|zero_sum;
endmodule

