# BPMtoOSC
Finally an easy, reliable and free way to keep the Resolume BPM in sync.
Just open the program, enter your resolume IP, set your audio input and hit start!

Since I was looking for something like this to avoid standing there the whole night smashing the spacebar and couldn't find anything samiliar, especially for free, I too matters into my own hands.
The app detects the beats per minute from an audio input and sending (custom) OSC commands to set the BPM-Counter inside Resolume (or any other LJ / VJ Software with OSC input).


If you want to change the OSC commands that are sent or any problems occur, edit or delete the
`%Appdata%\Roaming\BPMtoOSC\lastsession.ini` file.


<a href="url"><img src="https://user-images.githubusercontent.com/8715042/204784228-d0d6669f-5fe1-4689-aa9a-840369e1eebe.gif" align="center" width="500" ></a>


In case you want to edit the code yourself, make sure to use Python 3.9.13 and the package-versions defined in the requirements.txt file.

The beat detection itself was inspired and relies on the work from [DrLuke](https://github.com/DrLuke/aubio-beat-osc).



# BPMtoOSC
Finalmente, uma maneira fácil, confiável e gratuita de manter o BPM do Resolume sincronizado. Basta abrir o programa, inserir seu IP do Resolume, configurar sua entrada de áudio e clicar em Iniciar!

Como eu estava procurando algo assim para evitar ficar a noite toda apertando a barra de espaço e não encontrar nada parecido, especialmente de graça, também me dediquei a isso. O aplicativo detecta as batidas por minuto de uma entrada de áudio e envia comandos OSC (personalizados) para definir o contador de BPM dentro do Resolume (ou qualquer outro software LJ/VJ com entrada OSC).

Se você quiser alterar os comandos OSC enviados ou se ocorrer algum problema, edite ou exclua o arquivo %Appdata%\Roaming\BPMtoOSC\lastsession.ini.



Caso queira editar o código você mesmo, certifique-se de usar o Python 3.9.13 e as versões de pacote definidas no arquivo requirements.txt.

 A detecção de batidas em si foi inspirada e se baseia no trabalho do DrLuke.
