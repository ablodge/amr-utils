# amr-utils
A python package of common operations for AMRs


I wrote amr-utils to store operations that I often need when doing research with AMRs. Use it to load multiple AMRs from a text file, iterate through nodes or named entities, and output them into a useful format.

# HTML
Amr-utils allows you to read AMRs from a text file and output them as html. You can look in `style.css` for an example of styling. 
![latex example](https://github.com/ablodge/amr-utils/blob/master/html_ex.PNG)

The html above is generated from the following output.

```
<pre>
(<span class="amr-node" tok-id="c">c/cause-01</span>
      <span class="amr-edge" tok-id="c_ARG0_a">:ARG0</span> (<span class="amr-node" tok-id="a">a/and</span>
            <span class="amr-edge" tok-id="a_op1_h">:op1</span> (<span class="amr-node" tok-id="h">h/highway</span>
                  <span class="amr-edge" tok-id="h_ARG1-of_c2">:ARG1-of</span> (<span class="amr-node" tok-id="c2">c2/crowd-01</span>))
            <span class="amr-edge" tok-id="a_op2_t">:op2</span> (<span class="amr-node" tok-id="t">t/traffic</span>
                  <span class="amr-edge" tok-id="t_mod_r">:mod</span> (<span class="amr-node" tok-id="r">r/road</span>)
                  <span class="amr-edge" tok-id="t_ARG1-of_c3">:ARG1-of</span> (<span class="amr-node" tok-id="c3">c3/complicate-01</span>)))
      <span class="amr-edge" tok-id="c_ARG1_e">:ARG1</span> (<span class="amr-node" tok-id="e">e/expect-01</span>
            <span class="amr-edge" tok-id="e_ARG0_p">:ARG0</span> (<span class="amr-node" tok-id="p">p/person</span>)
            <span class="amr-edge" tok-id="e_ARG1_t2">:ARG1</span> (<span class="amr-node" tok-id="t2">t2/thing</span>
                  <span class="amr-edge" tok-id="t2_mod_g">:mod</span> (<span class="amr-node" tok-id="g">g/great</span>
                        <span class="amr-edge" tok-id="g_degree_m">:degree</span> (<span class="amr-node" tok-id="m">m/more</span>)))
            <span class="amr-edge" tok-id="e_topic_d">:topic</span> (<span class="amr-node" tok-id="d">d/develop-02</span>
                  <span class="amr-edge" tok-id="d_ARG1_s">:ARG1</span> (<span class="amr-node" tok-id="s">s/subway</span>)))
      <span class="amr-edge" tok-id="c_time_m2">:time</span> (<span class="amr-node" tok-id="m2">m2/meanwhile</span>))
</pre>
```


# Latex
Amr-utils allows you to read AMRs from a text file and output them as latex diagrams, such as the following.
![latex example](https://github.com/ablodge/amr-utils/blob/master/latex_ex.PNG)
